from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

from .models import db, t_prices, Port, Region


def _prepare_port_subquery(parent_region, cte_name):
    topq = db.session.query(Region)
    topq = topq.filter(Region.slug == parent_region)
    topq = topq.cte(cte_name, recursive=True)

    bottomq = db.session.query(Region)
    bottomq = bottomq.join(topq, Region.parent_slug == topq.c.slug)

    recursive_q = topq.union(bottomq)
    q = db.session.query(recursive_q).subquery()
    return db.session.query(Port.code).join(q, Port.parent_slug == q.c.slug).subquery()


def average_rates_query(date_from, date_to, origin, destination):
    destination_port_subquery = _prepare_port_subquery(destination, 'dest')
    origin_port_subquery = _prepare_port_subquery(origin, 'org')

    query = db.session.query(t_prices.c.day, func.avg(t_prices.c.price).label('average'))

    query = query.filter(and_(t_prices.c.day <= date_to,
                              t_prices.c.day >= date_from))
    query = query.filter(or_(origin == t_prices.c.orig_code,
                             t_prices.c.orig_code.in_(origin_port_subquery)))
    query = query.filter(or_(destination == t_prices.c.dest_code,
                             t_prices.c.dest_code.in_(destination_port_subquery)))

    query = query.group_by(t_prices.c.day)

    return query


def average_rates_query_null(date_from, date_to, origin, destination):
    raw_query = f"""
        WITH RECURSIVE org(slug, name, parent_slug) AS 
        (
           SELECT
              regions.slug AS slug,
              regions.name AS name,
              regions.parent_slug AS parent_slug 
           FROM
              regions 
           WHERE
              regions.slug = '{origin}' 
           UNION
           SELECT
              regions.slug AS regions_slug,
              regions.name AS regions_name,
              regions.parent_slug AS regions_parent_slug 
           FROM
              regions 
              JOIN
                 org 
                 ON regions.parent_slug = org.slug
        )
        ,
        dest(slug, name, parent_slug) AS 
        (
           SELECT
              regions.slug AS slug,
              regions.name AS name,
              regions.parent_slug AS parent_slug 
           FROM
              regions 
           WHERE
              regions.slug = '{destination}' 
           UNION
           SELECT
              regions.slug AS regions_slug,
              regions.name AS regions_name,
              regions.parent_slug AS regions_parent_slug 
           FROM
              regions 
              JOIN
                 dest 
                 ON regions.parent_slug = dest.slug
        )
        SELECT
           prices.day AS prices_day,
           (
              CASE
                 WHEN
                    COUNT(*) < 3 
                 THEN
                    NULL 
                 ELSE
                    avg(prices.price) 
              END
           )
           AS average 
        FROM
           prices 
        WHERE
           prices.day <= '{date_to}' 
           AND prices.day >= '{date_from}' 
           AND 
           (
              prices.orig_code = '{origin}' 
              OR prices.orig_code IN 
              (
                 SELECT
                    ports.code 
                 FROM
                    ports 
                    JOIN
                       (
                          SELECT
                             org.slug AS slug,
                             org.name AS name,
                             org.parent_slug AS parent_slug 
                          FROM
                             org
                       )
                       AS anon_1 
                       ON ports.parent_slug = anon_1.slug
              )
           )
           AND 
           (
              prices.dest_code = '{destination}' 
              OR prices.dest_code IN 
              (
                 SELECT
                    ports.code 
                 FROM
                    ports 
                    JOIN
                       (
                          SELECT
                             dest.slug AS slug,
                             dest.name AS name,
                             dest.parent_slug AS parent_slug 
                          FROM
                             dest
                       )
                       AS anon_2 
                       ON ports.parent_slug = anon_2.slug
              )
           )
        GROUP BY
           prices.day
    """

    return db.engine.execute(raw_query)


def insert_price(date_from, date_to, origin_code, destination_code, price):
    insert_statement = t_prices.insert().values(**{
        'day': date_to,
        'price': price,
        'orig_code': origin_code,
        'dest_code': destination_code
    })

    try:
        db.session.execute(insert_statement)
        db.session.commit()
    except IntegrityError as e:
        return 'destination or origin code not in registered ports'
    except Exception:
        return 'Error occurred while creating record'

    return 'success'
