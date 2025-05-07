#!/usr/bin/env python3
# Corso di Programmazione di Reti - Laboratorio - Università di Bologna
# Socket_Programming_Assignment - WebServer

from socket import *
import os
import threading

# Configurazione del server
serverPort = 8080
DOCUMENT_ROOT = 'www'
BUFFER_SIZE = 1024

def get_mime_type(file_path):
    """Determina il MIME type basato sull'estensione del file"""
    extension = os.path.splitext(file_path)[1].lower()
    
    # Dizionario di MIME types comuni
    mime_types = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.txt': 'text/plain'
    }
    
    return mime_types.get(extension, 'application/octet-stream')

def log_request(client_address, request_line, status_code):
    """Registra la richiesta nella console"""
    print(f"{client_address[0]}:{client_address[1]} - {request_line} - {status_code}")

def handle_client(connectionSocket, addr):
    """Gestisce una singola connessione client"""
    try:
        # Ricezione della richiesta
        message = connectionSocket.recv(BUFFER_SIZE)
        
        if not message:
            return
        
        # Parsing della richiesta
        request_data = message.decode('utf-8')
        request_lines = request_data.split('\n')
        request_line = request_lines[0]
        words = request_line.split()
        
        if len(words) < 3:
            return
            
        method, path, version = words
        
        print(message, '::', words[0], ':', words[1])
        
        # Gestione solo delle richieste GET
        if method != 'GET':
            response = "HTTP/1.1 405 Method Not Allowed\r\n\r\n"
            connectionSocket.send(response.encode('utf-8'))
            log_request(addr, request_line, "405 Method Not Allowed")
            return
            
        # Normalizzazione del percorso
        if path == '/':
            path = '/index.html'
            
        print(path, '||', path[1:])
        
        # Costruzione del percorso completo del file
        file_path = os.path.join(DOCUMENT_ROOT, path.lstrip('/'))
        
        # Verifica che il file esista e sia all'interno della directory www
        if not os.path.exists(file_path) or not os.path.isfile(file_path) or not os.path.abspath(file_path).startswith(os.path.abspath(DOCUMENT_ROOT)):
            # File non trovato o percorso non valido
            connectionSocket.send(bytes("HTTP/1.1 404 Not Found\r\n\r\n", "UTF-8"))
            connectionSocket.send(bytes("<html><head><title>404 Not Found</title></head><body><h1>404 Not Found</h1><p>La pagina richiesta non esiste.</p></body></html>\r\n", "UTF-8"))
            
            log_request(addr, request_line, "404 Not Found")
            connectionSocket.close()
            return
            
        # Lettura del file richiesto
        try:
            with open(file_path, 'r+') as f:
                outputdata = f.read()
                
            print(outputdata)
                
            # Determinazione del MIME type
            mime_type = get_mime_type(file_path)
                
            # Invio dell'header e del contenuto
            connectionSocket.send("HTTP/1.1 200 OK\r\n".encode())
            connectionSocket.send(f"Content-Type: {mime_type}\r\n".encode())
            connectionSocket.send(f"Content-Length: {len(outputdata)}\r\n\r\n".encode())
            connectionSocket.send(outputdata.encode())
            connectionSocket.send("\r\n".encode())
            
            log_request(addr, request_line, "200 OK")
                
        except IOError:
            # Errore durante la lettura del file
            connectionSocket.send(bytes("HTTP/1.1 500 Internal Server Error\r\n\r\n", "UTF-8"))
            connectionSocket.send(bytes("<html><head><title>500 Internal Server Error</title></head><body><h1>500 Internal Server Error</h1></body></html>\r\n", "UTF-8"))
            
            log_request(addr, request_line, "500 Internal Server Error")
            
    except Exception as e:
        print(f"Errore nella gestione del client: {str(e)}")
    finally:
        connectionSocket.close()

def main():
    """Funzione principale che avvia il server"""
    # Inizializzazione del server socket
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    
    try:
        # Creazione della directory www se non esiste
        if not os.path.exists(DOCUMENT_ROOT):
            os.makedirs(DOCUMENT_ROOT)
            print(f"Creata directory {DOCUMENT_ROOT}")
            
        # Binding del socket all'indirizzo e porta specificati
        server_address = ('localhost', serverPort)
        serverSocket.bind(server_address)
        
        # Inizio dell'ascolto di connessioni in entrata
        serverSocket.listen(1)
        print('the web server is up on port:', serverPort)
        
        # Ciclo principale del server
        while True:
            print('Ready to serve...')
            # Accettazione di nuove connessioni
            connectionSocket, addr = serverSocket.accept()
            print(connectionSocket, addr)
            
            # Gestione della connessione in un thread separato
            client_thread = threading.Thread(target=handle_client, args=(connectionSocket, addr))
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        print("\nServer arrestato.")
    except Exception as e:
        print(f"Errore del server: {str(e)}")
    finally:
        serverSocket.close()

if __name__ == "__main__":
    main()