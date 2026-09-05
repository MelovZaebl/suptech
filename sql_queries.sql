-- a) Выведи ники клиентов, поставивших csat меньше 3;

SELECT c.username
FROM clients c
JOIN tickets t ON c.username = t.ticket_client
WHERE t.csat < 3;

-- б) Напиши SQL запрос, который вернет id тикетов, в тексте которых содержится слово “отлично” и отсортируй их по убыванию ксата;

SELECT ticket_id
FROM tickets
WHERE text LIKE '%отлично%'
ORDER BY csat DESC;

-- в) Напиши SQL запрос, который вернет id клиентов, сделавших больше пяти заказов в ресторанах “Теремок” и “Вкусно и точка” на сумму от двух до десяти тысяч рублей. Также запрос должен вернуть сумму их самого дорогого заказа для этого фильтра. Полученные столбцы назови “frequent_customer” и “max_sum”;

SELECT
  o.order_client_id AS frequent_customer,
  MAX(o.price) AS max_sum
FROM orders o
WHERE o.place IN ('Теремок', 'Вкусно и точка')
  AND o.price BETWEEN 2000 AND 10000
GROUP BY o.order_client_id
HAVING COUNT(o.order_id) > 5;

-- г) Напиши SQL запрос, который дополнит таблицу orders данными из таблиц clients и tickets и вернет только 1000 записей из полученной таблицы.

SELECT *
FROM orders o
LEFT JOIN clients c ON o.order_client_id = c.client_id
LEFT JOIN tickets t ON t.ticket_order_id = o.order_id
LIMIT 1000;
