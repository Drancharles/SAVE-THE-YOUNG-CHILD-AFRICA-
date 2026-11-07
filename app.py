import os
import hmac
import sqlite3
import requests
from flask import Flask, request, jsonify, render_template_string, Response

# ===== CONFIG (secrets come from environment variables, not the code) =====
NOTIFY_EMAIL = "drancharles@gmail.com"
AIRTEL = "0740736550"
MTN = "0787918904"
WEB3FORMS_KEY = os.environ.get("WEB3FORMS_KEY", "")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
DB_FILE = os.environ.get("DB_FILE", "save_the_young.db")
LOCATION = "Namayumba, Buwasa Village, Wakiso District, Uganda"

app = Flask(__name__)


# ===== DATABASE =====
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS donations (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "donor_name TEXT, donor_email TEXT, amount TEXT, message TEXT, "
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "name TEXT, email TEXT, message TEXT, "
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    conn.close()


init_db()


# ===== EMAIL (sent from the server, so the key is never shown to visitors) =====
def send_notification(subject, body):
    if not WEB3FORMS_KEY:
        print("[EMAIL SKIPPED] WEB3FORMS_KEY not set")
        return False
    try:
        payload = {
            "access_key": WEB3FORMS_KEY,
            "subject": subject,
            "from_name": "Save The Young Website",
            "message": body,
        }
        r = requests.post("https://api.web3forms.com/submit", json=payload, timeout=20)
        print(f"[EMAIL] {subject} -> {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


# ===== ADMIN PASSWORD PROTECTION =====
def admin_ok():
    if not ADMIN_PASSWORD:
        return False
    auth = request.authorization
    if not auth:
        return False
    user_ok = hmac.compare_digest(auth.username or "", ADMIN_USER)
    pass_ok = hmac.compare_digest(auth.password or "", ADMIN_PASSWORD)
    return user_ok and pass_ok


def need_login():
    return Response(
        "Login required", 401, {"WWW-Authenticate": 'Basic realm="Save The Young Admin"'}
    )


# ===== PAGE LAYOUT =====
BASE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} - Save The Young Uganda</title>
<style>
body{margin:0;font-family:Arial,sans-serif;line-height:1.7;background:#f8fafc;color:#1e293b}
header{background:#0f172a;color:#fff;padding:30px 15px;text-align:center}
header h1{margin:0;font-size:30px}
header p{color:#cbd5e1;margin:8px 0}
header a{color:#93c5fd;margin:0 10px;text-decoration:none;font-weight:bold}
.container{max-width:1000px;margin:20px auto;padding:15px}
.card{background:#fff;padding:28px;margin-bottom:20px;border-radius:14px;box-shadow:0 4px 12px rgba(0,0,0,.05)}
h2{color:#0f172a;border-left:5px solid #2563eb;padding-left:12px}
h3{color:#1e40af}
input,textarea{width:100%;padding:13px;margin-top:12px;border:1px solid #cbd5e1;border-radius:10px;box-sizing:border-box;font-size:15px}
button{background:#2563eb;color:#fff;border:0;padding:14px;width:100%;border-radius:10px;font-weight:bold;margin-top:12px;font-size:16px;cursor:pointer}
button:hover{background:#1d4ed8}
.donate-box{background:#fffbeb;border:2px solid #f59e0b;padding:24px;border-radius:14px}
.big{font-size:22px;font-weight:bold;background:#fff;padding:12px 18px;border-radius:10px;display:inline-block;margin:6px 0;border:1px solid #f59e0b}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:700px){.grid{grid-template-columns:1fr}}
.location{background:#f0fdf4;border:1px solid #22c55e;padding:18px;border-radius:12px}
.ok{color:green;font-weight:bold}.err{color:red;font-weight:bold}
</style></head><body>
<header>
<h1>🌟 SAVE THE YOUNG</h1>
<p>Supporting Vulnerable Children &amp; Youth in Uganda</p>
<p style="font-size:13px;color:#fde68a">📍 {{ location }}</p>
<div style="margin-top:12px"><a href="/">Home</a><a href="/donate">Donate</a><a href="/contact">Contact</a></div>
</header>
<div class="container">{{ content|safe }}</div>
<footer style="text-align:center;padding:30px;color:#64748b;font-size:14px">
<b>Save The Young</b><br>{{ location }}<br>
Email: {{ email }} | Airtel: {{ airtel }} | MTN: {{ mtn }}
</footer></body></html>"""


def page(title, body):
    ctx = dict(airtel=AIRTEL, mtn=MTN, email=NOTIFY_EMAIL, location=LOCATION)
    content = render_template_string(body, **ctx)
    return render_template_string(BASE, title=title, content=content, **ctx)


# ===== PAGES =====
HOME = """
<div class="card">
  <h2>Who We Are</h2>
  <p><b>Save The Young</b> is a youth-led community-based organization in
  <b>{{ location }}</b>, working to support, protect and educate vulnerable children:
  orphans, street children, and children affected by poverty, HIV/AIDS, violence and
  school dropout.</p>
  <p>We believe every child deserves love, education, protection and a chance to dream again.</p>
  <!-- Add your real, verifiable figures here (children supported, etc.) -->
</div>
<div class="card">
  <h2>Our Vision &amp; Mission</h2>
  <h3>Vision</h3>
  <p>A Uganda where no child sleeps hungry, no child is denied education, and every young person can become self-reliant.</p>
  <h3>Mission</h3>
  <p>To rescue, educate, feed and empower vulnerable children and youth through education support, feeding, protection, counseling and skills training.</p>
</div>
<div class="card">
  <h2>Our Programs</h2>
  <div class="grid">
    <div><h3>📚 Education Support</h3><p>School fees, uniforms and scholastic materials for orphans and children who dropped out.</p></div>
    <div><h3>🍲 Feeding &amp; Nutrition</h3><p>Regular meals and food parcels for children and families in need.</p></div>
    <div><h3>🏠 Child Protection</h3><p>Counseling, referral and family reintegration for children at risk.</p></div>
    <div><h3>🧵 Youth Skills</h3><p>Training in tailoring, hairdressing, carpentry, computers and agriculture.</p></div>
  </div>
</div>
<div class="card">
  <div class="donate-box">
    <h3>🤝 Support a Child Today</h3>
    <p><b>Airtel Money:</b></p><div class="big">{{ airtel }}</div>
    <p><b>MTN Mobile Money:</b></p><div class="big">{{ mtn }}</div>
    <p>After sending, please confirm your donation so we can thank you.</p>
    <a href="/donate"><button>Donate Now &amp; Confirm</button></a>
  </div>
</div>
"""

DONATE = """
<div class="card">
  <h2>Donate</h2>
  <p>Thank you for supporting children in {{ location }}.</p>
  <div class="donate-box">
    <h3>📱 Step 1: Send via Mobile Money</h3>
    <p><b>Airtel Money:</b></p><div class="big">{{ airtel }}</div>
    <p><b>MTN Mobile Money:</b></p><div class="big">{{ mtn }}</div>
  </div>
</div>
<div class="card">
  <h3>Step 2: Confirm Your Donation</h3>
  <input id="n" placeholder="Your Full Name *" maxlength="100">
  <input id="e" placeholder="Your Email (for receipt)" maxlength="100">
  <input id="a" placeholder="Amount Sent * e.g. 50000 UGX" maxlength="50">
  <textarea id="m" placeholder="Transaction ID and message *" rows="4" maxlength="1000"></textarea>
  <button onclick="sendDon()">Confirm My Donation</button>
  <p id="msg"></p>
</div>
<script>
async function sendDon(){
  var msg=document.getElementById('msg');
  var d={name:document.getElementById('n').value.trim(),
         email:document.getElementById('e').value.trim(),
         amount:document.getElementById('a').value.trim(),
         message:document.getElementById('m').value.trim()};
  if(!d.name||!d.amount){msg.className='err';msg.textContent='Please fill in your name and the amount.';return;}
  msg.className='';msg.textContent='Saving...';
  try{
    var r=await fetch('/api/donate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
    if(r.ok){msg.className='ok';msg.textContent='Thank you! Your donation has been recorded. God bless you.';}
    else{msg.className='err';msg.textContent='Failed. Please try again.';}
  }catch(x){msg.className='err';msg.textContent='Network error. Please try again.';}
}
</script>
"""

CONTACT = """
<div class="card">
  <h2>Contact Us</h2>
  <div class="location"><b>📍 Address:</b> {{ location }}</div>
  <p><b>📞 Phone / WhatsApp:</b> {{ airtel }} / {{ mtn }}<br><b>📧 Email:</b> {{ email }}</p>
  <h3>Send Us a Message</h3>
  <input id="n" placeholder="Your Full Name *" maxlength="100">
  <input id="e" placeholder="Your Email *" maxlength="100">
  <textarea id="m" placeholder="Your message *" rows="6" maxlength="2000"></textarea>
  <button onclick="sendCon()">Send Message</button>
  <p id="msg"></p>
</div>
<script>
async function sendCon(){
  var msg=document.getElementById('msg');
  var d={name:document.getElementById('n').value.trim(),
         email:document.getElementById('e').value.trim(),
         message:document.getElementById('m').value.trim()};
  if(!d.name||!d.message){msg.className='err';msg.textContent='Please fill in your name and message.';return;}
  msg.className='';msg.textContent='Sending...';
  try{
    var r=await fetch('/api/contact',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
    if(r.ok){msg.className='ok';msg.textContent='Message sent! We will reply soon.';}
    else{msg.className='err';msg.textContent='Failed. Please try again.';}
  }catch(x){msg.className='err';msg.textContent='Network error. Please try again.';}
}
</script>
"""

ADMIN = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Admin</title></head>
<body style="font-family:Arial;padding:20px">
<h1>Save The Young - Admin</h1>
<h2>Donations ({{ dons|length }})</h2>
{% for d in dons %}
<p style="background:#f1f5f9;padding:10px;border-radius:8px">{{ d.created_at }} | <b>{{ d.donor_name }}</b> | {{ d.amount }} | {{ d.donor_email }} | {{ d.message }}</p>
{% endfor %}
<h2>Messages ({{ msgs|length }})</h2>
{% for m in msgs %}
<p style="background:#fef9c3;padding:10px;border-radius:8px">{{ m.created_at }} | <b>{{ m.name }}</b> | {{ m.email }}<br>{{ m.message }}</p>
{% endfor %}
</body></html>"""


# ===== ROUTES =====
@app.route("/")
def home():
    return page("Home", HOME)


@app.route("/donate")
def donate():
    return page("Donate", DONATE)


@app.route("/contact")
def contact():
    return page("Contact", CONTACT)


@app.route("/health")
def health():
    return "ok", 200


def clean(value, limit):
    return str(value or "").strip()[:limit]


@app.route("/api/donate", methods=["POST"])
def api_donate():
    data = request.get_json(silent=True) or {}
    name = clean(data.get("name"), 100)
    email = clean(data.get("email"), 100)
    amount = clean(data.get("amount"), 50)
    message = clean(data.get("message"), 1000)
    if not name or not amount:
        return jsonify({"success": False, "error": "name and amount required"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO donations (donor_name, donor_email, amount, message) VALUES (?,?,?,?)",
        (name, email, amount, message),
    )
    conn.commit()
    conn.close()

    body = (
        "NEW DONATION - Save The Young\n\n"
        f"Donor Name: {name}\nDonor Email: {email}\nAmount: {amount}\n"
        f"Transaction Details: {message}\n\nPlease verify in Mobile Money and thank the donor."
    )
    send_notification(f"Donation {amount} from {name}", body)
    return jsonify({"success": True}), 200


@app.route("/api/contact", methods=["POST"])
def api_contact():
    data = request.get_json(silent=True) or {}
    name = clean(data.get("name"), 100)
    email = clean(data.get("email"), 100)
    message = clean(data.get("message"), 2000)
    if not name or not message:
        return jsonify({"success": False, "error": "name and message required"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO messages (name, email, message) VALUES (?,?,?)", (name, email, message)
    )
    conn.commit()
    conn.close()

    body = f"NEW CONTACT MESSAGE\n\nFrom: {name}\nEmail: {email}\nMessage: {message}"
    send_notification(f"Contact message from {name}", body)
    return jsonify({"success": True}), 200


@app.route("/admin")
def admin():
    if not ADMIN_PASSWORD:
        return "Admin disabled: set the ADMIN_PASSWORD environment variable.", 503
    if not admin_ok():
        return need_login()
    conn = get_db()
    dons = [dict(r) for r in conn.execute("SELECT * FROM donations ORDER BY id DESC")]
    msgs = [dict(r) for r in conn.execute("SELECT * FROM messages ORDER BY id DESC")]
    conn.close()
    return render_template_string(ADMIN, dons=dons, msgs=msgs)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
