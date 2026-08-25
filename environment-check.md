# Environment Check

## Cursor
Cursor installed and AI assistant tested successfully.

## Docker

Check Docker version:

docker --version

Result:

Docker version 29.7.2, build a7dcaa6

Run test container:

docker run hello-world

Result:

Hello from Docker!
This message shows that your installation appears to be working correctly.

## Localhost

Run nginx container:

docker run -d -p 8080:80 nginx

Check running containers:

docker ps

Service available at:

http://localhost:8080

Result: nginx welcome page opened successfully.

## ngrok tunnel

Run ngrok tunnel:

ngrok http 8080

Public URL:

https://guzzler-footrest-engulf.ngrok-free.dev

Result: nginx page was successfully accessible through the public ngrok URL.