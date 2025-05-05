#!/usr/bin/env python3
import socket as sk
import os
import threading

# Configurazione del server
HOST = 'localhost'
PORT = 8080
BUFFER_SIZE = 1024
DOCUMENT_ROOT = 'www'

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

def handle_client(client_socket, client_address):
    """Gestisce una singola connessione client"""
    try:
        # Ricezione della richiesta
        request_data = client_socket.recv(BUFFER_SIZE).decode('utf-8')
        
        if not request_data:
            return
        
        # Parsing della richiesta
        request_lines = request_data.split('\n')
        request_line = request_lines[0]
        words = request_line.split()
        
        if len(words) < 3:
            return
            
        method, path, version = words
        
        # Gestione solo delle richieste GET
        if method != 'GET':
            response = "HTTP/1.1 405 Method Not Allowed\r\n\r\n"
            client_socket.send(response.encode('utf-8'))
            log_request(client_address, request_line, "405 Method Not Allowed")
            return
            
        # Normalizzazione del percorso
        if path == '/':
            path = '/index.html'
            
        # Costruzione del percorso completo del file
        file_path = os.path.join(DOCUMENT_ROOT, path.lstrip('/'))
        
        # Verifica che il file esista e sia all'interno della directory www
        if not os.path.exists(file_path) or not os.path.isfile(file_path) or not os.path.abspath(file_path).startswith(os.path.abspath(DOCUMENT_ROOT)):
            # File non trovato o percorso non valido
            response = "HTTP/1.1 404 Not Found\r\n"
            response += "Content-Type: text/html\r\n\r\n"
            response += "<html><head><title>404 Not Found</title></head>"
            response += "<body><h1>404 Not Found</h1><p>La pagina richiesta non esiste.</p></body></html>"
            
            client_socket.send(response.encode('utf-8'))
            log_request(client_address, request_line, "404 Not Found")
            return
            
        # Lettura del file richiesto
        try:
            with open(file_path, 'rb') as file:
                content = file.read()
                
            # Determinazione del MIME type
            mime_type = get_mime_type(file_path)
                
            # Costruzione della risposta
            header = f"HTTP/1.1 200 OK\r\n"
            header += f"Content-Type: {mime_type}\r\n"
            header += f"Content-Length: {len(content)}\r\n"
            header += "\r\n"
            
            # Invio dell'header e del contenuto
            client_socket.send(header.encode('utf-8'))
            client_socket.send(content)
            
            log_request(client_address, request_line, "200 OK")
                
        except Exception as e:
            # Errore durante la lettura del file
            response = "HTTP/1.1 500 Internal Server Error\r\n"
            response += "Content-Type: text/html\r\n\r\n"
            response += "<html><head><title>500 Internal Server Error</title></head>"
            response += f"<body><h1>500 Internal Server Error</h1><p>{str(e)}</p></body></html>"
            
            client_socket.send(response.encode('utf-8'))
            log_request(client_address, request_line, "500 Internal Server Error")
            
    except Exception as e:
        print(f"Errore nella gestione del client: {str(e)}")
    finally:
        client_socket.close()

def main():
    """Funzione principale che avvia il server"""
    # Inizializzazione del server socket
    server_socket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
    server_socket.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
    
    try:
        # Binding del socket all'indirizzo e porta specificati
        server_socket.bind((HOST, PORT))
        
        # Inizio dell'ascolto di connessioni in entrata
        server_socket.listen(5)
        print(f"Server HTTP in ascolto su http://{HOST}:{PORT}")
        
        # Creazione della directory www se non esiste
        if not os.path.exists(DOCUMENT_ROOT):
            os.makedirs(DOCUMENT_ROOT)
            print(f"Creata directory {DOCUMENT_ROOT}")
            
        # Ciclo principale del server
        while True:
            # Accettazione di nuove connessioni
            client_socket, client_address = server_socket.accept()
            
            # Gestione della connessione in un thread separato
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        print("\nServer arrestato.")
    except Exception as e:
        print(f"Errore del server: {str(e)}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()