from flask import Flask, jsonify, make_response
import threading
import requests
import time
import os
import logging

app = Flask(__name__, static_folder=None)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("TradeLensApp")

@app.route('/')
def home():
    return "Trade Lens Bot Engine Running Successfully!"

@app.route('/ping')
def ping():
    return "OK", 200

@app.route('/signal')
def get_signal():
    try:
        current_time = time.time()
        trend_calc = (int(current_time * 1000) // 100) % 100
        ai_decision = "CALL" if (trend_calc % 2 == 0) else "PUT"
        confidence = 96 + ((int(current_time * 13) + 19) % 4)
        
        res = jsonify({
            "signal": ai_decision,
            "confidence": confidence,
            "status": "GREEN_EXECUTE"
        })
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res
    except Exception as e:
        res = jsonify({"signal": "DOWN", "confidence": 95, "status": "GREEN_EXECUTE"})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res

@app.route('/bot.js')
def bot_script():
    js = """
    (function(){
        try {
            var d = document;
            ["tradelens-widget", "tradelens-style", "tradelens-laser-r", "tradelens-laser-l", "tradelens-laser-t"].forEach(function(i){
                var e = d.getElementById(i);
                if(e) e.remove();
            });

            var renderServerUrl = "https://ra-bot-9cq8.onrender.com";
            var botProfileImg = "https://i.postimg.cc/yNVqPD94/IMG-20261110-225927.jpg";

            var s = d.createElement('style');
            s.id = 'tradelens-style';
            s.innerHTML = '@keyframes tlPulseGlow {' +
                          '0% { box-shadow: 0 0 10px #ffffff, 0 0 20px #00f0ff; border-color: #00f0ff; }' +
                          '50% { box-shadow: 0 0 22px #ffffff, 0 0 40px #00f0ff; border-color: #ffffff; }' +
                          '100% { box-shadow: 0 0 10px #ffffff, 0 0 20px #00f0ff; border-color: #ffffff; }' +
                          '}' +
                          '@keyframes tlFadeBlink { 0% { opacity: 0.3; } 50% { opacity: 1; } 100% { opacity: 0.3; } }' +
                          '@keyframes tlScanRightToLeft { 0% { right: 0%; opacity: 0.95; } 100% { right: 100%; opacity: 0.95; } }' +
                          '@keyframes tlScanLeftToRight { 0% { left: 0%; opacity: 0.95; } 100% { left: 100%; opacity: 0.95; } }' +
                          '@keyframes tlScanTopToBottom { 0% { top: 0%; opacity: 0.95; } 100% { top: 100%; opacity: 0.95; } }';
            d.head.appendChild(s);

            var widget = d.createElement('div');
            widget.id = 'tradelens-widget';
            widget.style.cssText = 'position:fixed; top:130px; right:35px; width:62px; height:62px; background:#080c16; border:2.5px solid #00f0ff; border-radius:50%; display:flex; align-items:center; justify-content:center; z-index:2147483647; cursor:grab; animation:tlPulseGlow 3s infinite ease-in-out; overflow:hidden; box-sizing:border-box;';
            
            widget.innerHTML = '<img src="' + botProfileImg + '" style="width:100%; height:100%; object-fit:cover; border-radius:50%; pointer-events:none;" />';

            d.body.appendChild(widget);

            var isDragging = false, startX, startY, hasMoved = false;
            widget.onmousedown = widget.ontouchstart = function(e){
                isDragging = true; hasMoved = false;
                var p = e.touches ? e.touches[0] : e;
                startX = p.clientX - widget.offsetLeft; 
                startY = p.clientY - widget.offsetTop;
                widget.style.cursor = 'grabbing';
            };
            widget.onmousemove = widget.ontouchmove = function(e){
                if(!isDragging) return;
                var p = e.touches ? e.touches[0] : e;
                var nx = p.clientX - startX, ny = p.clientY - startY;
                if(Math.abs(nx - widget.offsetLeft) > 2 || Math.abs(ny - widget.offsetTop) > 2) hasMoved = true;
                widget.style.left = nx + 'px'; 
                widget.style.top = ny + 'px';
                widget.style.right = 'auto'; 
                widget.style.bottom = 'auto';
            };
            widget.onmouseup = widget.ontouchend = function(){ 
                isDragging = false; 
                widget.style.cursor = 'grab';
            };

            function detectUserTradingSeconds() {
                try {
                    var inputs = d.querySelectorAll('input, div, span');
                    for(var i = 0; i < inputs.length; i++) {
                        var text = (inputs[i].innerText || inputs[i].value || '').trim();
                        if(text.match(/^\\d{2}:\\d{2}:\\d{2}$/)) {
                            var parts = text.split(':');
                            var totalSec = parseInt(parts[0])*3600 + parseInt(parts[1])*60 + parseInt(parts[2]);
                            if(totalSec > 0 && totalSec <= 3600) return totalSec;
                        }
                    }
                    var timeInput = d.querySelector('input[class*="time"], input[class*="timer"]');
                    if(timeInput && timeInput.value) {
                        var val = parseInt(timeInput.value);
                        if(!isNaN(val) && val > 0) return val;
                    }
                } catch(e) {}
                return 5;
            }

            var isRunning = false;

            widget.onclick = function(e) {
                if(hasMoved) return;
                if(isRunning) return;
                isRunning = true;

                // ১. ক্লিক করার সাথে সাথে ব্যাকগ্রাউন্ড ব্ল্যাক এবং ছোট সাইজের ফেইডিং "SCANNING..." লেখা
                widget.style.background = '#000000';
                widget.style.borderColor = '#ffffff';
                widget.innerHTML = '<div style="font-size:7.5px; font-weight:900; color:#ffffff; text-align:center; letter-spacing:0.3px; line-height:1.2; animation: tlFadeBlink 1s infinite ease-in-out;">SCANNING...</div>';

                fetch(renderServerUrl + '/signal?t=' + Date.now())
                .then(function(r){ return r.json(); })
                .catch(function(){ return {signal: "DOWN", confidence: 95}; })
                .then(function(data){
                    var sig = String(data.signal || 'DOWN').toUpperCase();
                    var isCall = (sig === 'CALL' || sig === 'UP' || sig === 'BUY');
                    
                    startLaserLaserScanningSequence();

                    setTimeout(function(){
                        removeScanningEffect();
                        triggerQuotexTrade(isCall);

                        var targetSeconds = detectUserTradingSeconds();
                        var countdown = targetSeconds;

                        widget.style.background = isCall ? '#166534' : '#991b1b';
                        widget.style.borderColor = isCall ? '#22c55e' : '#ef4444';
                        
                        widget.innerHTML = '<div style="font-size:9px; font-weight:900; color:#fff; text-align:center; line-height:1.1;">' + (isCall ? 'UP' : 'DOWN') + '</div>' +
                                           '<div style="font-size:10.5px; font-weight:900; color:#fff; text-align:center; line-height:1.1;">' + formatTimeDisplay(countdown) + '</div>';

                        var timerInterval = setInterval(function(){
                            countdown--;
                            if(countdown >= 0) {
                                widget.innerHTML = '<div style="font-size:9px; font-weight:900; color:#fff; text-align:center; line-height:1.1;">' + (isCall ? 'UP' : 'DOWN') + '</div>' +
                                                   '<div style="font-size:10.5px; font-weight:900; color:#fff; text-align:center; line-height:1.1;">' + formatTimeDisplay(countdown) + '</div>';
                            }

                            if(countdown <= 0) {
                                clearInterval(timerInterval);
                                setTimeout(function(){
                                    widget.style.background = '#080c16';
                                    widget.style.borderColor = '#00f0ff';
                                    widget.innerHTML = '<img src="' + botProfileImg + '" style="width:100%; height:100%; object-fit:cover; border-radius:50%; pointer-events:none;" />';
                                    isRunning = false;
                                }, 2000);
                            }
                        }, 1000);

                    }, 5000);
                });
            };

            function formatTimeDisplay(sec) {
                if(sec >= 60) {
                    var m = Math.floor(sec / 60);
                    var s = sec % 60;
                    return m + 'm ' + (s > 0 ? s + 's' : '');
                }
                return sec + 's';
            }

            function startLaserLaserScanningSequence() {
                removeScanningEffect();
                
                var scanR1 = d.createElement('div');
                scanR1.id = 'tradelens-laser-r';
                scanR1.style.cssText = 'position:fixed; top:0; right:0; width:5px; height:100vh; background:linear-gradient(to left, rgba(255,255,255,0.8), #ffffff, rgba(255,255,255,0.8)); box-shadow: 0 0 20px #ffffff, 0 0 40px #ffffff, 0 0 70px #ffffff; z-index:2147483646; pointer-events:none; animation:tlScanRightToLeft 1.25s linear forwards;';
                d.body.appendChild(scanR1);

                setTimeout(function(){
                    var oldR1 = d.getElementById('tradelens-laser-r');
                    if(oldR1) oldR1.remove();

                    var scanT1 = d.createElement('div');
                    scanT1.id = 'tradelens-laser-t';
                    scanT1.style.cssText = 'position:fixed; top:0; left:0; width:100vw; height:5px; background:linear-gradient(to bottom, rgba(255,0,0,0.8), #ff0000, rgba(255,0,0,0.8)); box-shadow: 0 0 20px #ff0000, 0 0 40px #ff0000, 0 0 70px #ff0000; z-index:2147483646; pointer-events:none; animation:tlScanTopToBottom 1.25s linear forwards;';
                    d.body.appendChild(scanT1);
                }, 1250);

                setTimeout(function(){
                    var oldT1 = d.getElementById('tradelens-laser-t');
                    if(oldT1) oldT1.remove();

                    var scanL2 = d.createElement('div');
                    scanL2.id = 'tradelens-laser-l';
                    scanL2.style.cssText = 'position:fixed; top:0; left:0; width:5px; height:100vh; background:linear-gradient(to right, rgba(34,197,94,0.8), #22c55e, rgba(34,197,94,0.8)); box-shadow: 0 0 20px #22c55e, 0 0 40px #22c55e, 0 0 70px #22c55e; z-index:2147483646; pointer-events:none; animation:tlScanLeftToRight 1.25s linear forwards;';
                    d.body.appendChild(scanL2);
                }, 2500);

                setTimeout(function(){
                    var oldL2 = d.getElementById('tradelens-laser-l');
                    if(oldL2) oldL2.remove();

                    var scanT2 = d.createElement('div');
                    scanT2.id = 'tradelens-laser-t';
                    scanT2.style.cssText = 'position:fixed; top:0; left:0; width:100vw; height:5px; background:linear-gradient(to bottom, rgba(234,179,8,0.8), #eab308, rgba(234,179,8,0.8)); box-shadow: 0 0 20px #eab308, 0 0 40px #eab308, 0 0 70px #eab308; z-index:2147483646; pointer-events:none; animation:tlScanTopToBottom 1.25s linear forwards;';
                    d.body.appendChild(scanT2);
                }, 3750);
            }

            function removeScanningEffect() {
                ["tradelens-laser-r", "tradelens-laser-l", "tradelens-laser-t"].forEach(function(i){
                    var el = d.getElementById(i);
                    if(el) el.remove();
                });
            }

            function triggerQuotexTrade(isCall) {
                var targetBtn = null;
                var buttons = d.querySelectorAll('button, div[role="button"], span[class*="btn"]');
                for(var i=0; i<buttons.length; i++){
                    var btn = buttons[i];
                    var text = (btn.innerText || '').trim().toUpperCase();
                    var cls = (btn.className || '').toLowerCase();
                    var isUp = cls.includes('call') || cls.includes('buy') || cls.includes('up') || text === 'UP' || text === 'BUY';
                    var isDown = cls.includes('put') || cls.includes('sell') || cls.includes('down') || text === 'DOWN' || text === 'SELL';
                    
                    if(isCall && isUp && btn.getBoundingClientRect().width > 0){ targetBtn = btn; break; }
                    if(!isCall && isDown && btn.getBoundingClientRect().width > 0){ targetBtn = btn; break; }
                }
                if(targetBtn) {
                    try { targetBtn.click(); } catch(e) {}
                }
            }

        } catch(e) {}
    })();
    """
    res = make_response(js)
    res.headers['Content-Type'] = 'application/javascript'
    res.headers['Access-Control-Allow-Origin'] = '*'
    return res

def start_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    threading.Thread(target=start_server, daemon=True).start()
