from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from pathlib import Path
import json

results = json.loads(Path('docs/performance_results.json').read_text())
doc = Document()
section=doc.sections[0]
section.top_margin=Inches(.57);section.bottom_margin=Inches(.56)
section.left_margin=Inches(.72);section.right_margin=Inches(.72)
styles=doc.styles
styles['Normal'].font.name='Aptos';styles['Normal'].font.size=Pt(9.3)
styles['Normal'].paragraph_format.space_after=Pt(3)
for name, size in [('Title',15),('Heading 1',11),('Heading 2',10)]:
    s=styles[name];s.font.name='Aptos';s.font.size=Pt(size);s.font.bold=True;s.font.color.rgb=RGBColor(32,64,94)

title=doc.add_paragraph(style='Title');title.alignment=WD_ALIGN_PARAGRAPH.CENTER;title.add_run('HealthTrack Phase 3: Security and Performance Review')
sub=doc.add_paragraph();sub.alignment=WD_ALIGN_PARAGRAPH.CENTER
sub.add_run('Shawn Miller  |  MSCS-699-B01  |  University of the Cumberlands\nInstructor: Michael Solomon  |  November 8, 2026')

doc.add_heading('Project overview',level=1)
doc.add_paragraph('Phase 3 turns the HealthTrack design into a working FastAPI backend for a small, consent-based hypertension-monitoring pilot. The implemented tables center on patients, blood pressure and pulse readings, and daily activity records. Supporting accounts, care-team assignments, and audit events allow the project to demonstrate who can access each record. This is a local school project using fictional patients, not a system ready for clinical use.')

doc.add_heading('Security measures implemented',level=1)
doc.add_paragraph('The API requires a signed bearer token for protected routes. Demo passwords are stored as salted PBKDF2 hashes rather than plain text. Tokens expire after 30 minutes, and the service checks whether accounts are active. Role and ownership checks limit patient records to their owners, while nurses and clinicians can only access patients assigned to them. Administrators can manage enrollment and assignments but cannot access vital-sign or activity endpoints.')
doc.add_paragraph('Input checks reject underage enrollment, invalid blood pressure values, out-of-range pulse or activity entries, future-dated records, and missing timezones for readings. The database also enforces key value ranges, foreign keys, and unique daily activity records. New measurements require active enrollment and monitoring consent. Generic audit records capture key access and changes without storing measurement values in the audit text. Errors return clear HTTP status codes, and database integrity conflicts trigger a rollback.')

doc.add_heading('Important security limitations',level=1)
doc.add_paragraph('The current authentication uses a local demonstration JWT issuer rather than the trusted OpenID Connect provider proposed in Phase 2. MFA, request rate limiting, secure hosting and TLS setup, managed encryption, recovery testing, immutable reading revisions, complete denied-request audits, and a clinic-level privacy assessment remain unfinished. The DELETE endpoints were included to meet the CRUD requirement, but a real clinic would need an approved records-retention process instead of unrestricted hard deletion. No real patient data should be entered into this version.')

doc.add_page_break()
doc.add_heading('Testing and performance results',level=1)
doc.add_paragraph('All 33 automated tests passed, with no failed tests and 94% total application statement coverage. Tests covered model constraints, invalid inputs, authorization, consent, CRUD operations, date filters, missing records, duplicate activity entries, and audit creation. Both Alembic migrations were applied successfully to a local SQLite database.')

p=doc.add_paragraph()
p.add_run('Local database benchmark. ').bold=True
p.add_run(f"A synthetic SQLite dataset included {results['vital_rows']:,} vital records and {results['activity_rows']:,} activity records. Across {results['queries']} date-filtered queries returning up to {results['page_size']} readings, median retrieval time was {results['median_ms']:.3f} ms, 95th-percentile time was {results['p95_ms']:.3f} ms, and maximum observed time was {results['maximum_ms']:.3f} ms. These measurements reflect one machine and a direct database microbenchmark, not API throughput or production concurrency.")

doc.add_heading('Conclusion and next steps',level=1)
doc.add_paragraph('The prototype meets the main Phase 3 implementation goals: organized SQLAlchemy models, a reusable data-access layer, documented FastAPI endpoints, migration scripts, and testable access rules. Next steps are to replace demo authentication with external identity management and MFA, enforce full clinic isolation and retention rules, complete revision and alert workflows, and test with a production-like database and concurrent API requests. These improvements would be necessary before considering any clinical pilot.')

footer=section.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
footer.add_run('HealthTrack Phase 3  •  Educational prototype  •  Fictional data only').italic=True
out='docs/phase3_security_performance_report.docx'
doc.save(out)
print(out)
