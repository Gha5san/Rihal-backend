# Test suite 
Still not completed

## To run

From root directory:

```
docker-compose up -d --build
```
Then
```
docker-compose exec fastapi pytest tests
```
---

#### Note
There is only one test at the moment.

#### TODO

* Add tests for all endpoints
* Use separate db (maybe by using docker anonyms volumes?)
* Use mocking, stubs and faking