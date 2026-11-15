"""Dash/Plotly patient monitoring dashboard; integrated with Phase 3 records."""
from datetime import datetime
from dash import Dash, dcc, html, Input, Output, State, no_update, clientside_callback
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from app.database import SessionLocal
from app.models import User
from app.security import verify_password, make_token, current_user
from dashboard.monitor import allowed_patients, snapshot

dashboard = Dash(__name__, requests_pathname_prefix="/dashboard/",
                 routes_pathname_prefix="/", title="HealthTrack Monitor",
                 suppress_callback_exceptions=True)

def empty_chart(title):
    fig = go.Figure()
    fig.update_layout(title=title, template="plotly_white",
                      margin=dict(l=35,r=15,t=50,b=40), height=280,
                      paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
    return fig

dashboard.layout = html.Div([
    dcc.Store(id="auth", storage_type="session"),
    dcc.Store(id="live-store"),
    html.Header([
        html.Div([html.H1("HealthTrack"), html.P("Real-time patient monitoring • Educational demonstration")]),
        html.Span("SIMULATED / NON-CLINICAL", className="badge")
    ], className="header"),
    html.Section([
        html.Div([
            html.Label("Username", htmlFor="username"),
            dcc.Input(id="username", type="text", placeholder="demo_nurse", autoComplete="username"),
            html.Label("Password", htmlFor="password"),
            dcc.Input(id="password", type="password", placeholder="Password", autoComplete="current-password"),
            html.Button("Sign in", id="login", n_clicks=0, className="primary"),
            html.Button("Sign out", id="logout", n_clicks=0),
            html.Div(id="login-message", role="status"),
        ], className="login"),
        html.Div([
            html.Label("Patient", htmlFor="patient"),
            dcc.Dropdown(id="patient", options=[], placeholder="Sign in to select a patient"),
            html.P(id="connection", role="status", children="Disconnected"),
            html.P(id="refreshed", className="muted"),
        ], className="patient-select")
    ], className="toolbar"),
    html.Div(id="alert", role="alert", className="alert neutral", children="Sign in to view monitoring data."),
    html.Div([
        html.Div([html.Span("Systolic"),html.Strong(id="systolic", children="—"),html.Small("mmHg")],className="stat"),
        html.Div([html.Span("Diastolic"),html.Strong(id="diastolic", children="—"),html.Small("mmHg")],className="stat"),
        html.Div([html.Span("Pulse"),html.Strong(id="pulse", children="—"),html.Small("bpm")],className="stat"),
        html.Div([html.Span("Steps (latest day)"),html.Strong(id="steps", children="—"),html.Small("steps")],className="stat"),
        html.Div([html.Span("Active minutes"),html.Strong(id="minutes", children="—"),html.Small("minutes")],className="stat"),
    ], className="stats"),
    html.Div([
        dcc.Graph(id="pressure-graph", figure=empty_chart("Blood pressure trend"), config={"displayModeBar":False}),
        dcc.Graph(id="pulse-graph", figure=empty_chart("Pulse trend"), config={"displayModeBar":False}),
        dcc.Graph(id="activity-graph", figure=empty_chart("Daily steps"), config={"displayModeBar":False}),
    ], className="charts"),
    dcc.Interval(id="fallback", interval=10000, n_intervals=0),
    html.Footer("Training demonstration only. Thresholds are illustrative and are not medical advice.")
], className="page")

@dashboard.callback(Output("auth","data"), Output("login-message","children"),
                    Input("login","n_clicks"), Input("logout","n_clicks"),
                    State("username","value"), State("password","value"),
                    prevent_initial_call=True)
def login(login_clicks, logout_clicks, username, password):
    from dash import ctx
    if ctx.triggered_id == "logout":
        return None, "Signed out."
    with SessionLocal() as db:
        user = db.query(User).filter_by(username=username or "").first()
        if not user or not user.active or not password or not verify_password(password,user.password_hash):
            return None, "Invalid username or password."
        if user.role == "admin":
            return None, "Admin accounts cannot view patient charts."
        return {"token":make_token(user)}, "Signed in. Choose a patient."

@dashboard.callback(Output("patient","options"), Output("patient","value"),
                    Input("auth","data"))
def patients(auth):
    if not auth:
        return [], None
    with SessionLocal() as db:
        try:
            user = current_user(token=auth["token"], db=db)
            options = [{"label":p.full_name+" (#"+str(p.id)+")","value":p.id}
                       for p in allowed_patients(db,user) if p.enrolled and p.monitoring_consent]
            return options, (options[0]["value"] if options else None)
        except Exception:
            return [], None

# A browser WebSocket pushes updates into the Dash Store. A ten-second secure
# polling fallback recovers when a firewall/proxy disables WebSockets.
clientside_callback(
    """function(auth,patient) {
        if(window.healthtrackConnect) window.healthtrackConnect(auth && auth.token,patient);
        return window.dash_clientside.no_update;
    }""",
    Output("connection","title"), Input("auth","data"), Input("patient","value")
)

@dashboard.callback(Output("live-store","data",allow_duplicate=True),
                    Input("fallback","n_intervals"), State("auth","data"),State("patient","value"),
                    prevent_initial_call=True)
def poll(_tick, auth, patient_id):
    if not auth or not patient_id:
        raise PreventUpdate
    with SessionLocal() as db:
        try:
            user = current_user(token=auth["token"],db=db)
            data = snapshot(db,user,int(patient_id))
            if not data["enrolled"] or not data["consent"]:
                return {"error":"Monitoring consent or enrollment is inactive."}
            return data
        except Exception:
            return {"error":"Access expired or monitoring data unavailable. Sign in again."}

@dashboard.callback(Output("systolic","children"), Output("diastolic","children"),
                    Output("pulse","children"), Output("steps","children"),
                    Output("minutes","children"), Output("alert","children"),
                    Output("alert","className"), Output("pressure-graph","figure"),
                    Output("pulse-graph","figure"),Output("activity-graph","figure"),
                    Output("refreshed","children"),
                    Input("live-store","data"),Input("patient","value"),Input("auth","data"))
def render(data, selected_patient, auth):
    p = empty_chart("Blood pressure trend"); q = empty_chart("Pulse trend"); a = empty_chart("Daily steps")
    blank = ("—","—","—","—","—")
    if not auth or not data or data.get("patient_id") != selected_patient or data.get("error"):
        msg = (data.get("error") if data and data.get("error") else
               "Select a patient to begin. No measurements available yet.")
        return (*blank,msg,"alert neutral",p,q,a,"")
    readings = data["vitals"]; activities = data["activities"]; latest = data["latest"]
    if readings:
        xs=[v["measured_at"] for v in readings]
        p.add_trace(go.Scatter(x=xs,y=[v["systolic"] for v in readings],name="Systolic",mode="lines+markers"))
        p.add_trace(go.Scatter(x=xs,y=[v["diastolic"] for v in readings],name="Diastolic",mode="lines+markers"))
        p.add_hline(y=140,line_dash="dash",line_color="#e8a33e")
        q.add_trace(go.Scatter(x=xs,y=[v["pulse"] for v in readings],name="Pulse",mode="lines+markers"))
        q.add_hline(y=105,line_dash="dash",line_color="#e8a33e")
    if activities:
        a.add_trace(go.Bar(x=[v["date"] for v in activities],y=[v["steps"] for v in activities],name="Steps"))
    activity=activities[-1] if activities else None
    severity=data["severity"]
    status={"normal":"Latest reading is within demonstration thresholds.",
            "warning":"Warning: the latest reading is outside the demonstration range.",
            "critical":"Critical demonstration alert: the latest reading is outside the severe threshold.",
            "unknown":"No vital-sign measurements recorded."}[severity]
    return (latest["systolic"] if latest else "—",latest["diastolic"] if latest else "—",
            latest["pulse"] if latest else "—",activity["steps"] if activity else "—",
            activity["active_minutes"] if activity else "—",status,
            "alert "+severity,p,q,a,"Last checked: "+data["updated_at"])
