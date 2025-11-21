from waitress import serve
from need_to_do.wsgi import application

if __name__ == '__main__':
    serve(app=application, host='0.0.0.0', port=8090)