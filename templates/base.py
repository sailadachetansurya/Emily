"""Shared HTML layout for the Emily control panel."""

NAV_ITEMS = [
    ("/", "Overview", "&#8226;"),
    ("/pipeline", "Pipeline", "&#9654;"),
    ("/training", "Training", "&#8635;"),
    ("/config", "Settings", "&#9881;"),
    ("/logs", "Logs", "&#9776;"),
]


def render(page_title: str, active_path: str, body_html: str) -> str:
    nav_html = ""
    for href, label, icon in NAV_ITEMS:
        active = " active" if href == active_path else ""
        nav_html += f'<a class="nav-link{active}" href="{href}"><span class="nav-icon">{icon}</span>{label}</a>\n'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title} — Emily</title>
<link rel="stylesheet" href="/static/styles.css">
<script>
(function(){{
  var t=localStorage.getItem('emily-theme');
  if(t&&t!=='minimalist')document.body.className='theme-'+t;
}})();
</script>
</head>
<body>
<aside class="sidebar">
  <div class="sidebar-brand">
    <h1>Emily</h1>
    <span>Emotive AI</span>
  </div>
  <nav class="sidebar-nav">
    {nav_html}
  </nav>
  <div class="sidebar-footer">Pipeline v0.1.0</div>
</aside>
<main class="main fade-in">
{body_html}
</main>
<script src="/static/app.js"></script>
</body>
</html>"""
