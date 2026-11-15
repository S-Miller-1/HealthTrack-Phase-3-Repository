/* Connect with an existing session JWT; never embed credentials in a URL. */
(function () {
    let socket = null, active = "", retry = null;
    function indicator(text) {
        const el = document.getElementById("connection");
        if(el) el.textContent = text;
    }
    window.healthtrackConnect = function(token, patient) {
        const key = token && patient ? token + ":" + patient : "";
        if(key === active && socket && socket.readyState <= 1) return;
        active = key;
        if(retry) clearTimeout(retry);
        if(socket) { socket.onclose = null; socket.close(); socket = null; }
        if(!key) { indicator("Disconnected"); window.dash_clientside.set_props("live-store",{data:null}); return; }
        const url = (location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws/monitor";
        socket = new WebSocket(url);
        socket.onopen = function() {
            indicator("Live WebSocket connected");
            socket.send(JSON.stringify({token:token,patient_id:patient}));
        };
        socket.onmessage = function(ev) {
            try { window.dash_clientside.set_props("live-store",{data:JSON.parse(ev.data)}); }
            catch(e) { indicator("Unable to read live update"); }
        };
        socket.onclose = function() {
            indicator("Reconnecting • periodic refresh remains enabled");
            if(active === key) retry = setTimeout(function(){ window.healthtrackConnect(token, patient); }, 4000);
        };
        socket.onerror = function(){ indicator("WebSocket connection issue"); };
    };
})();