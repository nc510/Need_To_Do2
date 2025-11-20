from waitress import serve
from need_to_do.wsgi import application

if __name__ == '__main__':
    serve(app=application, host='127.0.0.1', port=8090)