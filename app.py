from flask import Flask, request, jsonify

app = Flask(__name__)

# متغير لتخزين أحدث قراءة استقبلناها من المحاكاة
latest_sensor_data = {
    "heart_rate": 0,
    "temperature": 0,
    "gsr": 0,
    "status": "Normal"
}

@app.route('/')
def home():
    return "Autism Stress Detection Backend is Running!"

# نقطة استقبال البيانات من محاكاة Wokwi
@app.route('/api/data', methods=['POST'])
def receive_data():
    global latest_sensor_data
    data = request.json
    
    if not data:
        return jsonify({"error": "No data received"}), 400
    
    latest_sensor_data = data
    print(f"Received -> HR: {data.get('heart_rate')}, Temp: {data.get('temperature')}, Status: {data.get('status')}")
    
    return jsonify({"status": "success"}), 200

# نقطة إرسال البيانات للواجهة الأمامية
@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(latest_sensor_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)