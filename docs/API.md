# API overview

## POST `/verify`

Request JSON:

```json
{
  "voter_id": "VOTER001",
  "image": "data:image/jpeg;base64,..."
}
```

Success:

```json
{
  "ok": true,
  "redirect": "/ballot"
}
```

## POST `/vote`

Form field:

```text
candidate_id=<integer>
```

The request requires a verified voter session.

## Administrative routes

- `GET/POST /admin/login`
- `GET /admin`
- `POST /admin/voters`
- `POST /admin/candidates`
- `GET /admin/results`
- `GET /admin/logout`
