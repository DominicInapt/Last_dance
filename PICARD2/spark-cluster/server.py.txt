# spark-cluster/server.py
from flask import Flask, request, Response
import subprocess

app = Flask(__name__)

@app.route('/execute', methods=['POST'])
def execute_script():
    data = request.json
    script_path = data.get('script_path')
    args = data.get('args', [])
    
    # We call standard python instead of spark-submit
    cmd = ['python', script_path] + args
    
    def generate_output():
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        # Stream the stdout line by line
        for line in iter(process.stdout.readline, ''):
            yield line
        
        process.wait()
        # Pass the exit code safely as the final string so Celery knows if it failed
        yield f"__EXIT_CODE__:{process.returncode}\n"
        
    return Response(generate_output(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)