### How to run
Setup docker and docker-compose on the machine.

run :

````docker-compose up````

This will automatically build and run the api client. The following endpoints have been implemented:

## Task 1

#### rates api

> Implement an API endpoint that takes the following parameters:
> 
>* date_from
>* date_to
>* origin
>* destination
>
>and returns a list with the average prices for each day on a route between port codes *origin* and *destination*.
>
>Both the *origin, destination* params accept either port codes or region slugs, making it possible to query for average prices per day between geographic groups of ports.
>
>    curl "http://127.0.0.1/rates?date_from=2016-01-01&date_to=2016-01-10&origin=CNSGH&destination=north_europe_main"
>
>    [
>        {
>            "day": "2016-01-01",
>            "average_price": 129
>        },
>        {
>            "day": "2016-01-02",
>            "average_price": 139
>        },
>        ...
>    ]


#### rates_null api

>Make a second API endpoint return an empty value (JSON null) for days
>on which there are less than 3 prices in total.
>
>    curl "http://127.0.0.1/rates_null?date_from=2016-01-01&date_to=2016-01-10&origin=CNSGH&destination=north_europe_main"
>
>    [
>        {
>            "day": "2016-01-01",
>            "average_price": 129
>        },
>        {
>            "day": "2016-01-02",
>            "average_price": null
>        },
>        {
>            "day": "2016-01-03",
>            "average_price": 215
>        },
>        ...
>    ]

#### upload_price api

> Implement an API endpoint where you can upload a price, including
> the following parameters:
> 
> * date_from
> * date_to
> * origin_code,
> * destination_code
> * price
> 

Since there's only date stored in the price table, I assumed this was an error in the requirements. Currently the 
api ignores the `date_from` value and only uses the value provided in `date_to`. Currency conversion is also supported
by this endpoint. Here's a sample request:

```
curl -X POST \
  http://127.0.0.1/upload_price \
  -H 'cache-control: no-cache' \
  -H 'content-type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW' \
  -H 'postman-token: e1cc5074-2d89-12d5-64b1-79aa8df479f4' \
  -F price=688 \
  -F destination_code=CNGGZ \
  -F origin_code=GBFXT \
  -F date_from=2016-01-22 \
  -F date_to=2016-01-22 \
  -F currency=EUR
```


## Task 2: Batch Processing Task

> Imagine you need to receive and update batches of tens of thousands of new prices, conforming to a similar format. Describe, using a couple of paragraphs, how you would design the system to be able to handle those requirements. Which factors do you need to take into consideration?

So from what I understand, the main concern here is failing constraints and the commit either roll-backing or not inserting past a certain value.

What we can do is we can use insert into an "UNLOGGED" table, then insert into the real table after checking if not constraints fail. Although this approach works
well for inserts, it doesn't work well for upsert/updates because there'd be concurrency issues. For those we might need to lock the table while perform the operation.

Unlogged tables are a faster alternative to temporary tables but the catch is that in the event of a server crash, you lose all data in the unlogged table unlike temporary tables.

Also we'll have to write a new api to handle this because such a large dataset would probably be sent over in a file (something like a CSV or JSON).
 