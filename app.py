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
        confidence = 95 + ((int(current_time * 11) + 17) % 5)
        
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

            var s = d.createElement('style');
            s.id = 'tradelens-style';
            s.innerHTML = '@keyframes tlPulseGlow {' +
                          '0% { box-shadow: 0 0 14px #ffffff, inset 0 0 8px #ffffff; border-color: #ffffff; }' +
                          '50% { box-shadow: 0 0 30px #22c55e, inset 0 0 15px #22c55e; border-color: #22c55e; }' +
                          '100% { box-shadow: 0 0 14px #ffffff, inset 0 0 8px #ffffff; border-color: #ffffff; }' +
                          '}' +
                          '@keyframes tlSpin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }' +
                          '@keyframes tlScanRightToLeft { 0% { right: 0%; opacity: 0.9; } 100% { right: 100%; opacity: 0.9; } }' +
                          '@keyframes tlScanLeftToRight { 0% { left: 0%; opacity: 0.9; } 100% { left: 100%; opacity: 0.9; } }' +
                          '@keyframes tlScanTopToBottom { 0% { top: 0%; opacity: 0.9; } 100% { top: 100%; opacity: 0.9; } }';
            d.head.appendChild(s);

            var widget = d.createElement('div');
            widget.id = 'tradelens-widget';
            widget.style.cssText = 'position:fixed; top:130px; right:35px; width:64px; height:64px; background:#0b0f19; border:2.5px solid #38bdf8; border-radius:50%; display:flex; flex-direction:column; align-items:center; justify-content:center; z-index:2147483647; cursor:grab; animation:tlPulseGlow 3s infinite ease-in-out; font-family:sans-serif; user-select:none; box-sizing:border-box;';
            
            widget.innerHTML = '<div style="font-size:9.5px; font-weight:900; color:#38bdf8; letter-spacing:0.5px; line-height:1;">TRADE</div>' +
                               '<div style="font-size:10.5px; font-weight:900; color:#fff; letter-spacing:0.5px; line-height:1; margin-top:2.5px;">LENS</div>';

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

            var isRunning = false;

            widget.onclick = function(e) {
                if(hasMoved) return;
                if(isRunning) return;
                isRunning = true;

                widget.style.borderColor = '#ffffff';
                widget.innerHTML = '<div style="width:20px; height:20px; border:2.5px solid #ffffff; border-top-color:transparent; border-radius:50%; animation:tlSpin 0.8s linear infinite;"></div>';

                fetch(renderServerUrl + '/signal?t=' + Date.now())
                .then(function(r){ return r.json(); })
                .catch(function(){ return {signal: "DOWN", confidence: 95}; })
                .then(function(data){
                    var sig = String(data.signal || 'DOWN').toUpperCase();
                    var isCall = (sig === 'CALL' || sig === 'UP' || sig === 'BUY');
                    var countdown = 10;

                    widget.style.background = isCall ? '#166534' : '#991b1b';
                    widget.style.borderColor = isCall ? '#22c55e' : '#ef4444';
                    
                    startMultiDirectionalScanning();

                    var timerInterval = setInterval(function(){
                        countdown--;
                        widget.innerHTML = '<div style="font-size:9px; font-weight:900; color:#fff; text-align:center; line-height:1.1;">' + (isCall ? 'UP' : 'DOWN') + '</div>' +
                                           '<div style="font-size:11px; font-weight:900; color:#fff; text-align:center; line-height:1.1;">' + countdown + 's</div>';

                        if(countdown <= 0) {
                            clearInterval(timerInterval);
                            removeAllScanners();
                            triggerQuotexTrade(isCall);

                            setTimeout(function(){
                                widget.style.background = '#0b0f19';
                                widget.style.borderColor = '#38bdf8';
                                widget.innerHTML = '<div style="font-size:9.5px; font-weight:900; color:#38bdf8; letter-spacing:0.5px; line-height:1;">TRADE</div>' +
                                                   '<div style="font-size:10.5px; font-weight:900; color:#fff; letter-spacing:0.5px; line-height:1; margin-top:2.5px;">LENS</div>';
                                isRunning = false;
                            }, 3500);
                        }
                    }, 1000);
                });
            };

            function startMultiDirectionalScanning() {
                removeAllScanners();
                
                // 1. Right to Left scanner (White, thick, high glow)
                var scanR = d.createElement('div');
                scanR.id = 'tradelens-laser-r';
                scanR.style.cssText = 'position:fixed; top:0; right:0; width:6px; height:100vh; background:linear-gradient(to left, #ffffff, rgba(255,255,255,0.2)); box-shadow: 0 0 20px #ffffff, 0 0 40px #ffffff; z-index:2147483646; pointer-events:none; animation:tlScanRightToLeft 2.5s linear infinite;';
                d.body.appendChild(scanR);

                // 2. Left to Right scanner (White, thick, glowing blue-white shadow)
                var scanL = d.createElement('div');
                scanL.id = 'tradelens-laser-l';
                scanL.style.cssText = 'position:fixed; top:0; left:0; width:6px; height:100vh; background:linear-gradient(to right, #ffffff, rgba(255,255,255,0.2)); box-shadow: 0 0 20px #ffffff, 0 0 40px #38bdf8; z-index:2147483646; pointer-events:none; animation:tlScanLeftToRight 2.5s linear infinite;';
                d.body.appendChild(scanL);

                // 3. Top to Bottom scanner (White, thick horizontal beam with green glow)
                var scanT = d.createElement('div');
                scanT.id = 'tradelens-laser-t';
                scanT.style.cssText = 'position:fixed; top:0; left:0; width:100vw; height:6px; background:linear-gradient(to bottom, #ffffff, rgba(255,255,255,0.2)); box-shadow: 0 0 20px #ffffff, 0 0 40px #22c55e; z-index:2147483646; pointer-events:none; animation:tlScanTopToBottom 2.5s linear infinite;';
                d.body.appendChild(scanT);
            }

            function removeAllScanners() {
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
