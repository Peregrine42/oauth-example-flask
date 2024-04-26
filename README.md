To start:

    1. pip install flask
    2. pip install requests
    3. populate the env vars in `.env.example` into a file called `.env`, e.g:

```
FLASK_APP=main
CLIENT_ID=
CLIENT_SECRET=
DOMAIN=<the address of the Auth server>
```

    3. flask --app main run
    4. navigate to: http://localhost:5000