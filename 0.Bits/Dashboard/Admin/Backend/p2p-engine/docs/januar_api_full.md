# Januar API Documentation (Full, Unredacted Conversion)



---

## Page 1

Introduction
Environments
Message format
Authentication
Accounts
Counterparty verification
Crypto
Crypto Terminology
List wallets
Get wallet
Create new Wallet
Submit withdrawal address
Update travel rule details for withdrawal address
Delete withdrawal address
List crypto transactions
Get crypto transaction
Initiate crypto withdrawal
Confirm withdrawal
Bitcoin Lightning and bolt11 memos
Create Bolt11 invoice - Bitcoin Lightning
Decode Bolt11 invoice - Bitcoin Lightning
Initiate payment of Bolt11 invoice - Bitcoin Lightning
Confirm payment of Bolt11 invoice - Bitcoin Lightning
Crypto data model
Crypto conversions
Crypto conversion details
Initiate crypto conversion
Confirm Crypto conversion
List crypto conversions
Get crypto conversion
Index data model
Notifications
Terminology for notifications
List notifications
create notification
update notification
Delete notification
Notification Data Model
Introduction
Welcome to Januar API! You can use our API to automate access to your payment accounts with Januar.
Please note that the Januar Customer API is under continuous development and while we seek not to change the public API in a way that would break clients, it is the responsibility
of client teams to ensure any documented API changes are adhered to when interacting with the Januar Customer API.
Swagger / OpenAPI
The Januar API also exist as Swagger UI and it's underlying OpenAPI specification which is available here
Environments
Januar provides two distinct environments available to the public:
Environment name
Base URL
Description
UAT
https://api.test.januar.com
Used for testing integrations
Production
https://api.januar.com
Live production environment


---

## Page 2

Message format
The Januar API uses JSON for both HTTP request and response payloads.
Success responses
Success response example where primary data is an object
{
  "data": {
    // ...
  },
  "metadata": {}
}
Success response example for a list endpoint
{
  "data": [
    // ...
  ],
  "metadata": {
    "pagination": {
      "pageSize": 100,
      "page": 0,
      "totalRecords": 1234
    }
  }
}
Whenever the API returns a success status code ( 2xx ), the response payload contains a JSON object with the following format:
Field
Type
Description
data
Object or Array
Primary data returned from the endpoint.
metadata
Object
Metadata about the response
↳ pagination
Object
(Optional) Pagination information, is defined in list endpoints.
  ↳ pageSize
Number
Maximum number of records returned per page in this response
  ↳ page
Number
Page number to retrieve, 0-indexed
  ↳ totalRecords
Number
Total number of records available
Error responses
Error format example
{
  "error": {
    "code": "ACCOUNT_INSUFFICIENT_BALANCE",
    "message": "Your account does not have sufficient balance to carry out this operation.",
    "context": {
      "requiredBalance": "123.45",
      "availableBalance": "100.00",
      "currency": "EUR"
    }
  },
  "sessionId": "ABC123ABC1234"
}
Default error payload for 401 Unauthorized
{
  "error": {
    "code": "INVALID_AUTHENTICATION",
    "message": "Authentication failed",
    "context": {}
  },
  "sessionId": "ABC123ABC1234"
}
Default error payload for 404 Not Found


---

## Page 3

{
  "error": {
    "code": "NOT_FOUND",
    "message": "The requested resource was not found",
    "context": {}
  },
  "sessionId": "ABC123ABC1234"
}
Whenever the API returns an error status code ( 4xx  for client errors, 5xx  for server errors), the response payload contains a JSON object with the following format (See example to the right):
Field
Type
Description
error
Object
Object describing the error that occurred.
↳ code
String
Machine-readable error code.
↳ messag
e
String
Human-friendly error message.
↳ contex
t
Object
Additional information related to the error. Object structure depends on the error code . Empty object if nothing.
sessionId
String
(Optional) session ID (also known as correlation ID) for the action. null  if error occurred in such a way that an ID could not be generated (never expected to
happen).
The Januar API uses the following HTTP error codes:
Error Code
Meaning
400 Bad Request
Bad Request -- Your request is invalid.
401 Unauthorized
Unauthorized -- Your authentication details are invalid. See Authentication section for more information
403 Forbidden
You are not allowed to access the specified resource.
404 Not Found
The specified resource could not be found.
500 Internal Server Error
We had a problem with our server. Try again later.
503 Service Unavailable
We're temporarily offline for maintenance. Please try again later.
Common data types
This section lists common data types that will be used throughout the API:
AMOUNT
All amounts are decimal numbers encoded as strings to avoid implicit precision errors when encoding/decoding the amounts.
An example is "203.10" .
PRECISION
All FIAT amounts are represented with a precision of 2 decimal places.
All crypto amounts are represented with a variable precision dependent on asset type (see below).
COUNTRY
All countries are represented by their * ISO 3166-1 alpha-2 country code*.
Examples include "DE"  for Germany, and "DK"  for Denmark.
CURRENCY
All fiat currencies are represented by their ISO 4217 currency code.
Examples include "EUR"  for Euro, and "DKK"  for Danish Krone.
IBAN
IBANs (International Bank Account Number) are defined in the ISO 13616 standard (Wikipedia IBAN page).
An example of a Danish IBAN is "DK8589000099106422" .
BIC CODE
BICs (Business Identifier Code) are represented by their * ISO 9362 code*.
An example of a Danish BIC is "SXPYDKKKXXX" .
TIMESTAMP
All timestamps are represented by a *ISO 8601 timestamp *.
An example is "2022-09-05T09:28:36Z" , meaning the timestamp 09:28:36 (UTC timezone) on September 5th, 2022.
Timestamps may include millisecond precision where applicable: "2022-09-05T09:28:36.420Z"


---

## Page 4

ASSETTYPE
All asset types are represented by a string.
The following crypto asset types are supported:
"BTC": Bitcoin, decimal precicion: 8 positions
"BTC_LN": Bitcoin on Lightning, decimal precision: 0 positions
"ETH": Ethereum, decimal precision: 18 positions
"USDC": USDC, decimal precision: 6 positions
"EURC": EURC, decimal precision: 6 positions
"USDT": USDT, decimal precision: 6 positions
"TRX": Tron, decimal precision: 6 positions
"SOL": Solana, decimal precision: 9 positions
Authentication
Example Authorization  header:
Authorization: JanuarAPI apikey="e871abb0-8a8d-4f6a-8551-7d34927af641", nonce="1660895358165", signature="oEp4bQXaYnRWG2XrbGfqeuGPEef6fokPjq9mA+gzBbE="
You must obtain an API key and secret pair to access our API. This key and secret pair must be used in the construction of every HTTP request to authenticate towards our API.
 Q: How do I obtain an API key and secret?
A: Please contact your Sales representative at Januar to get your API credentials
 API keys and associated secrets are specific to a particular environment. As an example, API keys issued in the UAT environment cannot be used in the production environment,
and vice versa.
In order to authenticate an HTTP request, it must include the following information in the Authorization  HTTP header:
apikey : API key
nonce : An integer that must increase with every successful request. It's common to use current Unix timestamp with millisecond precision for this.
signature : HMAC-SHA256  signature of request using API secret as key, encoded using base64
Signature generation
To generate a valid Authorization  header, use this code:
import base64
import hmac
import json
import time
import urllib.parse
from hashlib import sha256
method = 'POST'
account_id = 'cd74be8b-9f34-456e-86ee-15fa46a2a8b7'
path = '/accounts/' + account_id + '/transactions/payout'
encoded_path = urllib.parse.quote(path, safe='')
payload = {
  "amount": "12.45",
  "currency": "DKK",
  "iban": "GB15CLYD82663220400952",
  "paymentTime": "2023-05-25T11:43:00Z",
  "message": "Transfer to Acme customer",
  "name": "James Robert",
  "internalNote": "message to myself"
}
api_key = "e871abb0-8a8d-4f6a-8551-7d34927af641"
api_secret = "d39e5f5d-281e-4917-a878-8392dedaaf55"
nonce = 1660895358165  # use int(time.time() * 1000) for current Unix timestamp
message_to_sign = f"{nonce}|{method}|{encoded_path}|{json.dumps(payload)}".encode(
        "utf-8")
sha256_HMAC = hmac.new(api_secret.encode("utf-8"), message_to_sign,
                       digestmod=sha256)
signature = base64.b64encode(sha256_HMAC.digest()).decode()
auth_header = f'Authorization: JanuarAPI apikey="{api_key}", nonce="{nonce}", signature="{signature}"'
print(auth_header)
# Output
# Authorization: JanuarAPI apikey="e871abb0-8a8d-4f6a-8551-7d34927af641", nonce="1660895358165", signature="3Cr1HxM7ZNnAIFNehJ4FLbbHPvFFdE0xi8cFJ4tGiOE="
Make sure to replace apiKey  and apiSecret  with your API key and secret pair.
A valid request signature signs over the following parts of an HTTP request:


---

## Page 5

Nonce
Method: GET , POST , etc
Path including query string: e.g. /accounts/340975fd-fc40-4011-8f21-c8d6abd4a124/transactions?page=0&pageSize=1000
Body: e.g. {"action":"pay"} . If the request does not have a body, an empty string is used.
The signature is a HMAC-SHA256 of the concatenation of the nonce, method (uppercased), path (including query string) and body (if no body, empty string), separated by pipe character ( | ),
using the API secret as signing key, encoded with base64.
Authentication error
Authentication error object (HTTP status code will be 401 Unauthorized )
{
  "code": "IDENTITY_ACCESS_MANAGEMENT_CUSTOMER_UNAUTHORIZED",
  "message": "Customer is not authorized to access this resource",
  "context": {}
}
In case the Authorization  header is missing, api key doesn't exist, or the signature validation fails, any request will fail with a 401 Unauthorized  HTTP status code.
Accounts
Terminology
This section aims to provide a high-level overview of the different entities and concepts in the Accounts API
Concept
Description
Account
An account holds your balances in one or more currencies.
Balance
A balance is the amounts of available money in a single currency of a given account.
Transaction
A transaction in its basic form represents a group of account movements happening as one unit. It is specialized in multiple different sub types detailing individual
interactions that can happen on your account, e.g. a payout (See Types of transactions below).
TYPES OF TRANSACTIONS
Type
Description
Payin
A payin transaction is when money is received in your account from an external account.
Returned payin
A returned payin transaction is when a previously received payin transaction was returned to the sender.
Payout
A payout transaction is when money is sent from your account to an external account.
Returned payout
A returned payout transaction is when a previously sent payout transaction was returned to your account.
Currency conversion
A currency conversion transaction is when you convert money from one currency in your account to another currency in the same account.
Fee
A fee transaction is when your account is charged a stand-alone fee.
Returned fee
A returned fee transaction is when a previously paid fee transaction was returned to your account.
List accounts
Example 200 OK  response for GET /accounts
{
  "data": [
    {
      "id": "241a9346-1081-42c4-b0a0-a1e222709d19",
      "name": "System Account",
      "defaultCurrency": "EUR",
      "currencies": {
        "EUR": {
          "balance": "9755771.71"
        },
        "DKK": {
          "balance": "1005123.82"
        }
      },
      "balances": {
        "EUR": "9755771.71",
        "DKK": "1005123.82"
      },
      "accountNumbers": [


---

## Page 6

        {
          "iban": "DK8589000099106422",
          "country": "DK",
          "defaultCurrency": "EUR",
          "bank": {
            "name": "BANKING CIRCLE",
            "bic": "SXPYDKKKXXX",
            "addresses": [
              {
                "street": "Amerika Plads 38",
                "city": "København Ø",
                "region": null,
                "zip": "2100",
                "country": "DK"
              }
            ]
          },
          "bankIdentifier": "8900",
          "accountNumber": "0099106422",
          "supportedCurrencies": [
            "EUR"
          ],
          "supportedRails": [
            "SEPA_CREDIT",
            "SEPA_INSTANT"
          ]
        }
      ],
      "features": [
        {
          "accountFeatureType": "FX_ACCOUNT"
        }
      ]
    },
    ...
  ],
  "metadata": {
    "pagination": {
      "pageSize": 10,
      "page": 0,
      "totalRecords": 16
    }
  }
}
This endpoint retrieves all your accounts.
HTTP REQUEST
GET /accounts
QUERY PARAMETERS
Parameter
Description
pageSize
Positive integer determining how many accounts to return per page, max 10
page
Page number to retrieve, 0-indexed
HTTP RESPONSE
200 OK
The endpoint returns a paged list of account objects
Get account
Example 200 OK  response for GET /accounts/:accountId
{
  "data": {
    "id": "f27cd81e-27ef-43fd-9aaf-22abe65dd0c7",
    "name": "My account",
    "status": "active",
    "defaultCurrency": "EUR",
    "currencies": {
      "DKK": {
        "balance": "1175023.15"
      },
      "EUR": {
        "balance": "996225.43"
      }
    },
    "accountNumbers": [
      {
        "iban": "DK8589000099106422",
        "country": "DK",
        "defaultCurrency": "EUR",
        "bank": {
          "name": "BANKING CIRCLE",
          "bic": "SXPYDKKKXXX",
          "address": [
            {
              "street": "Amerika Plads 38",
              "zip": "2100",


---

## Page 7

              "city": "København Ø",
              "region": "Hovedstaden",
              "country": "DK"
            }
          ]
        }
      }
    ]
  },
  "metadata": {}
}
This endpoint retrieves an account.
HTTP REQUEST
GET /accounts/:accountId
PATH PARAMETERS
Parameter
Description
accountId
ID of the account to be retrieved.
HTTP RESPONSE
200 OK
The endpoint returns an account object
List transactions
This endpoint lists all transactions for a particular account, sorted by newest first.
Example 200 OK  response for GET /accounts/75db7319-d2fd-4610-98c2-201fbe49e6f3/transactions
{
  "data": [
    {
      "id": "814b3ab1-b997-40a3-8c63-5593518fb619",
      "accountId": "75db7319-d2fd-4610-98c2-201fbe49e6f3",
      "type": "PAYOUT",
      "currency": "EUR",
      "status": "COMPLETED",
      "amount": "-123.45",
      "feeAmount": "-0.10",
      "message": "Transfer to Acme customer",
      "internalNote": "message to myself",
      "counterparty": {
        "type": "LEGAL",
        "name": "Januar Aps",
        "accountNumber": "DE68500105178297336485",
        "accountNumberType": "IBAN",
        "accountNumberCountryCode": "DE"
      },
      "initiatedTime": "2022-08-17T11:31:43.868328Z",
      "paymentTime": "2022-08-31T10:00:00Z"
    },
    {
      // ... more transactions
    }
  ],
  "metadata": {
    "pagination": {
      "pageSize": 100,
      "page": 0,
      "totalRecords": 61
    }
  }
}
HTTP REQUEST
GET /accounts/:accountId/transactions
PATH PARAMETERS
Parameter
Description
accountId
ID of account to list transactions for.
QUERY PARAMETERS
Parameter
Default
Description
types
[]
If set, only return transactions of the given types
pageSize
100
Positive integer determining how many transactions to return per page, max 1000
page
0
Page number to retrieve, 0-indexed


---

## Page 8

Parameter
Default
Description
statuses
[]
List of payout Payout statuses to query. As statuses only apply to payouts, adding a status filter to the query, will result in only payouts will be returned. If not
provided, all types will be queried
dateFrom
null
Determines the earliest transactionTime of the transactions queried. Format YYYY-MM-DD
dateTo
null
Determines the latest transactionTime of the transactions queried. Format YYYY-MM-DD
amountFro
m
null
Determines the inclusive lower limit for the transaction amount
amountTo
null
Determines the inclusive upper limit for the transaction amount
currencie
s
[]
List of currencies code to query. If not provided, all transaction currencies will be queried
text
null
Search term. Will query in following fields message , counterparty.accountNumber , counterparty.name , internalNote
HTTP RESPONSE
200 OK
The endpoint returns a list of transactions
POSSIBLE ERRORS
HTTP Status code
error.code
Description
context
404 Not Found
ACCOUNT_NOT_FOUND
Account with ID :accountId  not found on customer: :customerId
None
400 Bad Request
BAD_REQUEST
Invalid value: :value  for field: :field
None
400 Bad Request
BAD_REQUEST
Type mismatch
None
400 Bad Request
CURRENCY_NOT_SUPPORTED
Invalid currency: :currency
None
Get transaction
This endpoint retrieves a transaction for a particular account.
Example 200 OK  response
for GET /accounts/75db7319-d2fd-4610-98c2-201fbe49e6f3/transactions/814b3ab1-b997-40a3-8c63-5593518fb619
{
  "data": {
    "id": "814b3ab1-b997-40a3-8c63-5593518fb619",
    "accountId": "75db7319-d2fd-4610-98c2-201fbe49e6f3",
    "type": "PAYOUT",
    "completedTime": "2023-03-26T01:00:08.806Z",
    "currency": "EUR",
    "status": "COMPLETED",
    "amount": "-123.45",
    "feeAmount": "0.00",
    "message": "Transfer to Acme customer",
    "internalNote": "message to myself",
    "counterparty": {
      "type": "LEGAL",
      "name": "Januar Aps",
      "accountNumber": "DE68500105178297336485",
      "accountNumberType": "IBAN",
      "accountNumberCountryCode": "DE"
    },
    "initiatedTime": "2023-03-21T10:51:40.415604Z",
    "paymentTime": "2023-03-26T11:51:40Z"
  },
  "metadata": {}
}
HTTP REQUEST
GET /accounts/:accountId/transactions/:transactionId
PATH PARAMETERS
Parameter
Description
accountId
ID of the account to list the transaction.
transactionId
ID of the transaction to be retrieved.
HTTP RESPONSE
200 OK
The endpoint returns a transaction
POSSIBLE ERRORS


---

## Page 9

HTTP Status code
error.code
Description
context
404 Not Found
ACCOUNT_NOT_FOUND
Account with ID :accountId  not found on customer: :customerId
None
400 Bad Request
BAD_REQUEST
Type mismatch
None
Initiate payout
This endpoint enables you to initiate a single payout.
NOTE: Payouts initiated through the API will auto-confirm, and thus begin in either the AWAITING_APPROVAL  or PENDING  status.
HTTP REQUEST
POST /accounts/:accountId/transactions/payout
Example request for initiating a payout at POST /accounts/:accountId/transactions/payout
{
  "amount": "10.01",
  "currency": "EUR",
  "paymentTime": "2022-09-16T06:00:00Z",
  "message": "Payment ref: #abcdef",
  "internalNote": "Payment for goods",
  "replayId": "#abcdef::efd9d6dc-4d38-4d61-a1be-5d8a9849ee44"
  "counterparty": {
    "type": "LEGAL",
    "name": "Januar Aps",
    "accountNumber": "DE68500105178297336485",
    "accountNumberType": "IBAN",
    "accountNumberCountryCode": "DE"
  }
}
PATH PARAMETERS
Parameter
Description
accountId
ID of account to initiate the payout for.
REQUEST BODY
Field
Type
Description
amount
Amount
The amount of the payout. Note the fee amount will be visible on the initiated payout instance.
currency
Currency
Currency of the payout.
paymentTime
Timestamp
(Optional) The future timestamp of when this payout should happen. If not specified it should happen now.
message
String
Message to the receiver.
internalNote
String
(Optional) Note only visible to the creator of the payout.
replayId
String
(Optional) Used to avoid a duplicate identical payout. Payout is rejected if replayId is re-used.
counterparty
Counterparty
Counterparty information.
↳ name
String
Name of the receiver of this payout
↳ accountNumber
String
Account number of the reciever - this can be an IBAN(ISO 13616:2020) or BBAN
↳ accountNumberType
String
Type of the account number - either IBAN  or BBAN
↳ accountNumberCountryCode
String
(Optional for IBANs) Country code of the account number
HTTP RESPONSE
Example 201 Created  response from initiate payout
{
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "accountId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "type": "PAYIN",
    "completedTime": "2022-11-12T12:34:56Z",
    "currency": "EUR",
    "status": "PENDING",
    "amount": "10.01",
    "feeAmount": "0.51",
    "message": "Payment ref: #abcdef",
    "internalNote": "Payment for goods",
    "initiatedTime": "2022-11-12T12:34:56Z",
    "paymentTime": "2022-11-12T12:34:56Z",
    "counterparty": {
      "type": "LEGAL",


---

## Page 10

      "name": "Januar Aps",
      "accountNumber": "DE68500105178297336485",
      "accountNumberType": "IBAN",
      "accountNumberCountryCode": "DE"
    }
  },
  "metadata": {}
}
201 CREATED
The endpoint returns a payout transaction
POSSIBLE ERRORS
HTTP Status code
error.code
Description
context
400 Bad Request
invalid-format
There was a formatting error in the request. See error message for details.
None
400 Bad Request
invalid-iban
Invalid IBAN specified.
None
400 Bad Request
insufficient-funds
There is insufficient funds available on the account to initiate the payout.
requiredBalance : the required balance for the payout
availableBalance : the available balance
currency : currency for the balances
400 Bad Request
invalid-payment-time
The paymentTime  must be in the future.
None
400 Bad Request
unsupported currency
Specified currency is not supported by the account.
None
404 Not found
account-not-found
Account with ID :accountId  could not be found.
None
Cancel payout
Example request for cancelling a payout at PUT /accounts/:accountId/transactions/payout/:payoutId/cancel
Example 200 OK  response from canceled payout
{
  "data": {
    "id": "67f8cbd2-166a-48b2-86e1-f0c46a426aa3",
    "accountId": "3fa8bac8-e173-4d49-8f68-18ec2bd52b2a",
    "type": "PAYOUT",
    "currency": "EUR",
    "status": "CANCELLED",
    "amount": "-123.45",
    "feeAmount": "-0.10",
    "message": "Transfer to Acme customer",
    "internalNote": "message to myself",
    "initiatedTime": "2022-09-05T10:45:12Z",
    "paymentTime": "2022-09-16T06:00:00Z",
    "counterparty": {
      "type": "LEGAL",
      "name": "Januar Aps",
      "accountNumber": "DE68500105178297336485",
      "accountNumberType": "IBAN",
      "accountNumberCountryCode": "DE"
    }
  },
  "metadata": {}
}
This endpoint enables you to cancel payouts.
NOTE: Only payouts with the status PENDING  or AWAITING_APPROVAL  are cancelable
HTTP REQUEST
PUT /accounts/:accountId/transactions/payout/:payoutId/cancel
PATH PARAMETERS
Parameter
Description
accountId
ID of account to initiate the payout for.
payoutId
ID of the payout to cancel
REQUEST BODY
The request body should be left empty
HTTP RESPONSE
200 OK
The endpoint returns a payout transaction with a CANCELLED  status
POSSIBLE ERRORS


---

## Page 11

HTTP Status code
error.code
Description
context
404 Not Found
ACCOUNT_NOT_FOUND
Account with ID :accountId  not found on customer: :customerId
None
404 Not Found
PAYOUT_NOT_FOUND
Payout with ID :payoutId  could not be found.
None
400 Bad Request
payout-not-cancelable
The specified payout is not cancelable as it is in a final state
None
400 Bad Request
BAD_REQUEST
Type mismatch
None
Accounts data model
This section describes the data model of each type of entity in the Accounts API:
Account
Transaction
Payin transaction
Returned Payin transaction
Payout transaction
Returned Payout transaction
Currency conversion transaction
Fee transaction
Returned Fee transaction
Bank
Address
ACCOUNT
Example account object
{
  "id": "241a9346-1081-42c4-b0a0-a1e222709d19",
  "name": "System Account",
  "defaultCurrency": "EUR",
  "currencies": {
    "EUR": {
      "balance": "9755771.71"
    },
    "DKK": {
      "balance": "1005123.82"
    }
  },
  "balances": {
    "EUR": "9755771.71",
    "DKK": "1005123.82"
  },
  "accountNumbers": [
    {
      "iban": "DK8589000099106422",
      "country": "DK",
      "defaultCurrency": "EUR",
      "bank": {
        "name": "BANKING CIRCLE",
        "bic": "SXPYDKKKXXX",
        "addresses": [
          {
            "street": "Amerika Plads 38",
            "city": "København Ø",
            "region": null,
            "zip": "2100",
            "country": "DK"
          }
        ]
      },
      "bankIdentifier": "8900",
      "accountNumber": "0099106422",
      "supportedCurrencies": [
        "EUR"
      ],
      "supportedRails": [
        "SEPA_CREDIT",
        "SEPA_INSTANT"
      ]
    }
  ],
  "features": [
    {
      "accountFeatureType": "FX_ACCOUNT"
    }
  ]
}
An account holds your balances in one or more currencies.
Field
Type
Description
id
String (UUID)
Unique identifier for the account
name
String
Name of account
status
String
Either ACTIVE  or INACTIVE


---

## Page 12

Field
Type
Description
defaultCurrency
Currency (DEPRECATED)
Currency code for account's default currency. Always corresponds to a key in the currencies  object.
currencies
Object (DEPRECATED)
Map of currencies supported by the account. Each key is a supported currency.
↳ currency
Object (DEPRECATED)
Single currency supported by the account.
  ↳ balance
String (DEPRECATED)
Balance for specific currency in the account.
balances
Object
Map of balances for each currency supported by the account. Each key is a supported currency.
↳ currency
String
Balance for specific currency in the account.
accountNumbers
Array
Account numbers associated with the account
↳ []
Object
A single account number object
  ↳ iban
IBAN
IBAN (International Bank Account Number)
  ↳ country
Country
Country of account number
  ↳ defaultCurrency
Currency
Default currency of account number.
  ↳ bank
Bank
Bank providing the account number
  ↳ bankIdentifier
String
Bank identifier (e.g., bank code)
  ↳ accountNumber
String
Local account number
  ↳ supportedCurrencies
Array
List of currencies supported by this account number
  ↳ supportedRails
Array
List of payment
features
Array
List of features enabled for this account
↳ []
Object
A single account feature object
TRANSACTION
Example transaction object of type PAYIN .
Note that the id , accountId , type , and completedTime  fields are present for all types of transactions, while the rest of the fields are specific for the PAYIN  transaction type.
{
  "id": "780e39f3-4fde-49c8-bd25-2ec2364fd01e",
  "accountId": "3fa8bac8-e173-4d49-8f68-18ec2bd52b2a",
  "type": "PAYIN",
  "completedTime": "2022-08-15T11:45:32Z",
  "currency": "EUR",
  "amount": "123.45",
  "feeAmount": "-0.10",
  "message": "Transfer from Acme customer",
  "counterparty": {
    "type": "LEGAL",
    "name": "Januar Aps",
    "accountNumber": "DE68500105178297336485",
    "accountNumberType": "IBAN",
    "accountNumberCountryCode": "DE"
  }
}
A transaction in its basic form represents a group of account movements happening as one unit. It is specialized in multiple different sub types detailing individual interactions that can
happen on your account, e.g. a payout.
A transaction has a number of base fields which are always included for any transaction type, as well as a number of fields which are type-specific. The base fields are defined first, and
subsequently each specific transaction type is documented:
Field
Type
Description
id
String (UUID)
Unique identifier for the transaction.
accountId
String (UUID)
Reference to the account that this transaction belongs to.
type
String
Type of transaction. This value should be used to determine which type-specific fields are included. See transaction types below.
completedTime
Timestamp
(Optional) Timestamp when the transaction was completed.
TRANSACTION TYPES
For a brief overview of the different transaction types, please refer to the terminology section above.
type
Transaction type
PAYIN
Payin
RETURNED_PAYIN
Returned Payin


---

## Page 13

type
Transaction type
PAYOUT
Payout
RETURNED_PAYOUT
Returned Payout
CURRENCY_CONVERSION
Currency conversion
FEE
Fee
RETURNED_FEE
Returned Fee
The above list of transaction types may expand in the future as we add more features. Please take care to handle unknown types appropriately.
PAYIN TRANSACTION ( PAYIN )
Example payin transaction object
{
  "id": "314b54a3-eb06-4dba-9032-9c06618763aa",
  "accountId": "3fa8bac8-e173-4d49-8f68-18ec2bd52b2a",
  "type": "PAYIN",
  "completedTime": "2022-08-15T11:45:32Z",
  "currency": "EUR",
  "amount": "123.45",
  "feeAmount": "-0.10",
  "message": "Transfer from Acme customer",
  "counterparty": {
    "type": "LEGAL",
    "name": "Januar Aps",
    "accountNumber": "DE68500105178297336485",
    "accountNumberType": "IBAN",
    "accountNumberCountryCode": "DE"
  }
}
A payin transaction is when money is received in your account from an external account. The account balance increases with the amount specified in the amount  field (subtracted an optional
feeAmount ).
Field
Type
Description
currency
Currency
Currency code for this payin
amount
Amount
Positive amount indicating the money received in the account.
feeAmount
Amount
Zero or negative amount indicating the amount deducted as a fee of this transaction.
message
String
Free-text description from the sender.
counterparty
Counterparty
Counterparty information.
↳ type
String
Type of counterparty - either LEGAL , PRIVATE  or UKNOWN  if we are missing type info
↳ name
String
Name of the receiver of this payout
↳ accountNumber
String
Account number of the receiver - this can be an IBAN(ISO 13616:2020) or BBAN
↳ accountNumberType
String
Type of the account number - either IBAN  or BBAN
↳ accountNumberCountryCode
String
(Optional for IBANs) Country code of the account number
RETURNED PAYIN TRANSACTION ( RETURNED_PAYIN )
Example returned payin transaction object
{
  "id": "c16f5074-132b-4d41-b5d7-c7ffdb8217e6",
  "accountId": "3fa8bac8-e173-4d49-8f68-18ec2bd52b2a",
  "payinId": "314b54a3-eb06-4dba-9032-9c06618763aa",
  "type": "RETURNED_PAYIN",
  "completedTime": "2022-08-15T11:45:32Z",
  "currency": "EUR",
  "amount": "-123.45",
  "feeAmount": "0.10"
}
A returned payin transaction is when a previously received payin transaction was returned to the sender.
Field
Type
Description
payinId
String (UUID)
Id of the original payin transaction that this transaction returns.
currency
Currency
Currency code for this returned payin
amount
Amount
Negative amount indicating the money subtracted from the account.


---

## Page 14

Field
Type
Description
feeAmount
Amount
Zero or positive amount indicating the amount added to the account.
PAYOUT TRANSACTION ( PAYOUT )
Example payout transaction object
{
  "id": "67f8cbd2-166a-48b2-86e1-f0c46a426aa3",
  "accountId": "3fa8bac8-e173-4d49-8f68-18ec2bd52b2a",
  "type": "PAYOUT",
  "completedTime": "2022-08-15T11:45:32Z",
  "paymentTime": "2022-08-15T11:40:12Z",
  "initiatedTime": "2022-08-15T11:40:12Z",
  "currency": "EUR",
  "status": "COMPLETED",
  "amount": "-123.45",
  "feeAmount": "-0.10",
  "message": "Transfer to Acme customer",
  "internalNote": "message to myself",
  "counterparty": {
    "type": "LEGAL",
    "name": "Januar Aps",
    "accountNumber": "DE68500105178297336485",
    "accountNumberType": "IBAN",
    "accountNumberCountryCode": "DE"
  }
}
A payout transaction is a payout from the account to an external account. The account balance decreased with the amount specified in the amount  field (including an optional feeAmount ).
Field
Type
Description
currency
Currency
Currency code for this payout
status
Payout status
Status of this payout
amount
Amount
Negative amount indicating the amount deducted from the account for this transaction.
feeAmount
Amount
Zero or negative amount indicating the fee amount deducted from the account.
message
String
Free-text message to the receiver.
internalNote
String
(Optional) Free-text internal note to oneself.
counterparty
Counterparty
Counterparty information.
↳ name
String
Name of the receiver of this payout
↳ accountNumber
String
Account number of the reciever - this can be an IBAN(ISO 13616:2020) or BBAN
↳ accountNumberType
String
Type of the account number - either IBAN  or BBAN
↳ accountNumberCountryCode
String
(Optional for IBANs) Country code of the account number
initiatedTime
Timestamp
Timestamp of when the payout was initiated in the account.
paymentTime
Timestamp
Timestamp of when the payout was set to happen (payout can be delayed for some reason).
PAYOUT STATUSES
A PAYOUT  transaction can have the following status  codes:
Status code
Description
Final state?
AWAITING_CONFIRMATION
The payout is awaiting confirmation from initiator. Only used when initiating from the web interface
No
AWAITING_APPROVAL
The payout is awaiting approval from an approver
No
PENDING
The payout is pending completion
No
CANCELLED
The payout was cancelled before it could complete
Yes
REJECTED
The payout was rejected
Yes
COMPLETED
The payout was successfully executed
Yes


---

## Page 15

PENDING
AWAITING_APPROVAL
AWAITING_CONFIRMATION
CANCELLED
REJECTED
COMPLETED
RETURNED PAYOUT TRANSACTION ( RETURNED_PAYOUT )
Example returned payout transaction object
{
  "id": "158315d3-3263-4906-839d-b755ef13498a",
  "accountId": "3fa8bac8-e173-4d49-8f68-18ec2bd52b2a",
  "payoutId": "67f8cbd2-166a-48b2-86e1-f0c46a426aa3",
  "type": "RETURNED_PAYOUT",
  "completedTime": "2022-08-15T11:45:32Z",
  "currency": "EUR",
  "amount": "123.45",
  "feeAmount": "0.10"
}
A returned payout transaction is when a previously sent payout transaction was returned to your account.
Field
Type
Description
payoutId
String (UUID)
Id of the original payout transaction that it returns.
currency
Currency
Currency code for this payout
amount
Amount
Positive amount indicating the amount added to the account as part of this returned payout.
feeAmount
Amount
Zero or positive amount indicating the fee amount returned as part of this returned payout.
CURRENCY CONVERSION TRANSACTION ( CURRENCY_CONVERSION )
Example currency conversion transaction object
{
  "id": "0223f4bd-3072-4387-9c46-b9f927ee756c",
  "accountId": "3fa8bac8-e173-4d49-8f68-18ec2bd52b2a",
  "type": "CURRENCY_CONVERSION",
  "completedTime": "2022-08-15T11:45:32Z",
  "sellCurrency": "EUR",
  "sellAmount": "-1000.00",
  "sellRate": "7.44123",
  "buyCurrency": "DKK",
  "buyAmount": "7441.23"
}
A currency conversion transaction is when you convert money from one currency (the sell currency) in your account to another currency (the buy currency) in the same account.
Field
Type
Description
sellCurrency
Currency
Currency code of the sell amount.
sellAmount
Amount
Negative amount indicating the amount deducted from the account.
sellRate
String
Rate of the currency conversion.
buyCurrency
Currency
Currency code of the buy amount.
buyAmount
Amount
Positive number indicating the buy amount added to the account.
FEE TRANSACTION ( FEE )
Example fee transaction object
{
  "id": "d4450c67-80a1-4244-9ed3-9ae07aa7c686",
  "accountId": "3fa8bac8-e173-4d49-8f68-18ec2bd52b2a",
  "type": "FEE",
  "completedTime": "2022-08-15T11:45:32Z",
  "currency": "EUR",
  "amount": "-99.90",


---

## Page 16

  "message": "Acme monthly subscription fee"
}
A fee transaction is when your account is charged a stand-alone fee.
Field
Type
Description
currency
Currency
Currency code for this fee.
amount
Amount
Negative amount indicating the amount deducted from the account from this fee transaction.
message
String
Message describing the fee to the receiver.
RETURNED FEE TRANSACTION ( RETURNED_FEE )
Example returned fee transaction object
{
  "id": "f3507542-edcf-4e8a-959d-3771fef2a380",
  "accountId": "3fa8bac8-e173-4d49-8f68-18ec2bd52b2a",
  "feeId": "90aac3f6-584b-4d3e-9d9c-a6c1332c74f5",
  "type": "RETURNED_FEE",
  "completedTime": "2022-08-15T11:45:32Z",
  "currency": "EUR",
  "amount": "99.90"
}
A returned fee transaction is when a previously paid fee transaction was returned to your account.
Field
Type
Description
feeId
String (UUID)
Id of the fee transaction that it returns.
currency
Currency
Currency code for this fee.
amount
Amount
Positive amount indicating the amount added to the account because of this returned fee transaction.
BANK
Example bank object
{
  "name": "BANKING CIRCLE",
  "bic": "SXPYDKKKXXX",
  "address": {
    "street": "Amerika Plads 38",
    "zip": "2100",
    "city": "København Ø",
    "region": "Hovedstaden",
    "country": "DK"
  }
}
A reference to a bank.
Field
Type
Description
name
String
Bank name
bic
BIC
BIC (Business Identifier Code) for bank
address
Address
Bank address
ADDRESS
Example address object
{
  "street": "Gothersgade 14",
  "zip": "1123",
  "city": "København",
  "region": "Hovedstaden",
  "country": "DK"
}
A reference to a physical address.
Field
Type
Description
street
String
Street address
zip
String
(Optional) Zip code
city
String
City
region
String
(Optional) Region country
country
Country
Country code.


---

## Page 17

Counterparty verification
Use the Counterparty verification endpoints to verify the payee (counterparty) details you intend to use for payments. This feature is aligned with the European Payments Council’s Verification
of Payee (VOP) scheme and helps reduce failed payments by ensuring the name/beneficiary details align with the target account.
The scheme allows the PSP of the payer (the Requesting PSP) to instantly send to the PSP of the payee (the Responding PSP), a request to verify the IBAN and the name of the payee as
given by the payer (the Requester). The reason for this request is that the payer intends to initiate a SEPA Credit Transfer (SCT) or a SEPA Instant Credit Transfer (SCT Inst) transaction to the
payee.
The Responding PSP will then instantly verify whether the received data match with the concerned data registered for that payee at the Responding PSP. The Responding PSP immediately
provides the Requesting PSP with a VOP response (e.g., match, no match, close match with the name of the payee, match/verification check not possible). The Requesting PSP then
immediately passes on the response to the payer.
The scheme provides PSPs with a messaging functionality. It is not a payment means or a payment instrument but it allows the payer to verify certain data about a payee. It cannot be relied
upon to identify a private or a legal person.
 Additional information about the EPC Verification of Payee scheme can be found on the official EPC website. See EPC – Verification of Payee for details.
Verify a counterparty
This endpoint initiates verification of a counterparty/payee.
Example request for POST /counterparty-verification
{
  "type": "LEGAL",
  "name": "Acme GmbH",
  "accountNumber": "DE68500105178297336485",
  "accountNumberType": "IBAN",
  "accountNumberCountryCode": "DE"
}
Example 201 CREATED response for POST /counterparty-verification
{
  "data": {
    "id": "f0b2d4a1-4d34-4e53-a01b-6f01d2b9a1ab",
    "counterparty": {
      "type": "LEGAL",
      "name": "Acme GmbH",
      "accountNumber": "DE68500105178297336485",
      "accountNumberType": "IBAN",
      "accountNumberCountryCode": "DE"
    },
    "status": "SUBMITTED",
    "result": null
  },
  "metadata": {}
}
HTTP REQUEST
POST /counterparty-verification
REQUEST BODY
Field
Type
Description
Validation rules
type
Enum
(Optional) Counterparty type. One of PRIVATE  or LEGAL .
If PRIVATE , surname  is required
name
String
Counterparty name. For type LEGAL  this is the company name. For type PRIVATE  this is the person's first name.
required , min length 1
surname
String
(Optional) Private person surname. Required if type  is PRIVATE .
accountNumber
String
Counterparty account number (e.g. IBAN or BBAN).
required , min length 1
accountNumberType
Enum
Counterparty account number type. One of IBAN  BBAN , UNKNOWN .
required , must be IBAN
accountNumberCountryCode
String
(Optional) Two-letter ISO country code of the account number (e.g. DE ).
length = 2
HTTP RESPONSE
201 CREATED
The endpoint returns a SuccessResponseCounterpartyVerificationDTO  with the newly created verification request. The status  will typically be INITIATED  or SUBMITTED  and result  may be
null receiving PSP has responded with the details of the lookup.
POSSIBLE ERRORS
HTTP Status Code
Description
400 Bad Request
Input validation error


---

## Page 18

HTTP Status Code
Description
401 Unauthorized
Authentication failed
404 Not Found
Resource not found
500 Internal Server Error
Unexpected error in the service
502 Bad Gateway
Upstream error
503 Service Unavailable
Service temporarily unavailable
Get counterparty verification status
Retrieves the status and result of a previously initiated counterparty verification.
Example 200 OK response for GET /counterparty-verification/:counterpartyVerificationId
{
  "data": {
    "id": "f0b2d4a1-4d34-4e53-a01b-6f01d2b9a1ab",
    "counterparty": {
      "type": "LEGAL",
      "name": "Acme GmbH",
      "accountNumber": "DE68500105178297336485",
      "accountNumberType": "IBAN",
      "accountNumberCountryCode": "DE"
    },
    "status": "COMPLETED",
    "result": {
      "code": "MATCH",
      "description": null
    }
  },
  "metadata": {}
}
HTTP REQUEST
GET /counterparty-verification/:counterpartyVerificationId
PATH PARAMETERS
Parameter
Type
Description
counterpartyVerificationId
UUID
ID of the counterparty verification to query
HTTP RESPONSE
200 OK
The endpoint returns a SuccessResponseCounterpartyVerificationDTO  containing a CounterpartyVerificationDTO . When status  is COMPLETED , the result  object will contain the outcome of
the verification.
POSSIBLE ERRORS
HTTP Status Code
Description
400 Bad Request
Input validation error
401 Unauthorized
Authentication failed
404 Not Found
Verification not found
500 Internal Server Error
Unexpected error in the service
502 Bad Gateway
Upstream error
503 Service Unavailable
Service temporarily unavailable
Data model
COUNTERPARTYVERIFICATION
Field
Type
Description
id
UUID
Unique identifier of the counterparty verification
counterparty
Counterparty
Details of the counterparty being verified
status
Enum
Current status of the verification: INITIATED , SUBMITTED , COMPLETED , FAILED
result
CounterpartyVerificationResult (nullable)
Result of the verification when completed


---

## Page 19

COUNTERPARTY
Field
Type
Description
type
Enum
(Optional) Counterparty type. One of PRIVATE  or LEGAL
name
String
Counterparty name – company name for LEGAL , first name for PRIVATE .
surname
String
(Optional) Private person surname. Required if type  is PRIVATE .
accountNumber
String
Counterparty account number
accountNumberType
Enum
Account number type: IBAN , BBAN , UNKNOWN
accountNumberCountryCode
String
(Optional) Two-letter ISO country code of the account number (e.g. DE )
COUNTERPARTYVERIFICATIONRESULT
Field
Type
Description
code
Enum
One of MATCH , CLOSE_MATCH , NO_MATCH , REJECTED , ERROR
descriptio
n
String
(Optional) Detailed description of the verification result. For CLOSE_MATCH  this may contain the matched counterparty name. For REJECTED / ERROR  it contains the
reason.
Crypto
Crypto Terminology
This section aims to provide a high-level overview of the different entities and concepts in the Crypto API
Concept
Description
Wallet
A wallet is a collection of crypto assets and withdrawal addresses.
Asset
An asset holds the amount available of a given crypto currency and its given deposit address.
Withdrawal
address
A withdrawal address is a whitelisted external crypto address not managed by Januar which can be used to withdraw assets to. This means that in order to
withdraw funds to a an external address, you need to create a withdrawal address beforehand, otherwise the withdrawal will be blocked by Januar. Read more
details in the withdrawal address section
Crypto
transaction
A crypto transaction is a INGOING or OUTGOING transfer of crypto assets.
Bolt11 Crypto
transaction
A Bolt11 crypto transaction is a INGOING or OUTGOING transfer of bitcoin on the Lightning network.
Satoshi
Smallest denominator in Bitcoin, used for Lightning network payments. 1 satoshi = 1/100.000.000 bitcoin
List wallets
Example 200 OK  response for GET /wallets
{
  "data": [
    {
      "id": "5f1a9b49-511b-40cf-a39f-0a4185947b53",
      "name": "Crypto Account",
      "withdrawalAddressTimeLockInMillis": 45000000,
      "assets": [
        {
          "assetType": "BTC_TEST",
          "assetName": "Bitcoin testnet",
          "assetDisplayName": "BTC Testnet",
          "balance": "0.0",
          "depositAddress": "tb1q6qteuwrat4yqur22zsqw7s04dyw7x386pquxmr"
        },
        {
          "assetType": "ETH_TEST5",
          "assetName": "Ethereum testnet (Sepolia)",
          "assetDisplayName": "ETH Sepolia",
          "balance": "0.0",
          "depositAddress": "0xF447703c2e349C1960c9876636Ab69295Ee36a4c"
        },
        {
          "assetType": "EURC_ETH_TEST5",
          "assetName": "Euro Coin (Circle) testnet (Sepolia)",
          "assetDisplayName": "EURC (ETH) Sepolia",
          "balance": "0.0",
          "depositAddress": "0xF447703c2e349C1960c9876636Ab69295Ee36a4c"
        },


---

## Page 20

        {
          "assetType": "SOL_TEST",
          "assetName": "Solana testnet",
          "assetDisplayName": "SOLANA Test",
          "balance": "0.0",
          "depositAddress": "7Pq6yXcRUBH3SeFYjmHpP4kKXzv4Nc8mhE2jZ8yZqxh8"
        },
        {
          "assetType": "TRX_TEST4",
          "assetName": "Tron testnet",
          "assetDisplayName": "TRX Shasta",
          "balance": "0.0",
          "depositAddress": "TYEqTVbsiZHdzF5cL4GbfsE2JmzcioL85E"
        },
        {
          "assetType": "USDC_TEST5",
          "assetName": "USDC testnet (Sepolia)",
          "assetDisplayName": "USDC Sepolia",
          "balance": "0.0",
          "depositAddress": "0xF447703c2e349C1960c9876636Ab69295Ee36a4c"
        },
        {
          "assetType": "USDT_TEST4",
          "assetName": "USDT Tron testnet",
          "assetDisplayName": "USDT Shasta",
          "balance": "0.0",
          "depositAddress": "TYEqTVbsiZHdzF5cL4GbfsE2JmzcioL85E"
        },
        {
          "assetType": "USDT_TEST5",
          "assetName": "USDT testnet (Sepolia)",
          "assetDisplayName": "USDT Sepolia",
          "balance": "0.0",
          "depositAddress": "0xF447703c2e349C1960c9876636Ab69295Ee36a4c"
        }
      ],
      "withdrawalAddresses": []
    }
  ],
  "metadata": {
    "pagination": {
      "pageSize": 1,
      "page": 1,
      "totalRecords": 6
    }
  }
}
This endpoint returns a wallet.
HTTP REQUEST
GET /wallets/
QUERY PARAMETERS
Parameter
Description
pageSize
Positive integer determining how many wallets to return per page, max 10
page
Page number to retrieve, 0-indexed
HTTP RESPONSE
The endpoint returns a paged list of wallet objects.
Get wallet
Example 200 OK  response for GET /wallets/3fa85f64-5717-4562-b3fc-2c963f66afa6
{
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "My wallet",
    "assets": [
      {
        "assetType": "ETH",
        "balance": "0.1",
        "depositAddress": "0x1234567890"
      }
    ],
    "withdrawalAddressTimeLockInMillis": 259200,
    "withdrawalAddresses": [
      {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "walletId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "label": "My Ether Wallet",
        "initiated": "2023-03-20T12:39:44.177Z",
        "validFrom": "2023-03-23T12:39:44.177Z",
        "destinationAddress": "0x1234567890abcdef1234567890abcdef12345678",
        "assetType": "ETH",
        "status": "ACTIVE"
      }
    ]
  },


---

## Page 21

  "metadata": {}
}
This endpoint returns a list of all your wallets.
HTTP REQUEST
GET /wallets/:walletId
HTTP RESPONSE
200 OK
The endpoint returns a wallet object.
Create new Wallet
This endpoint allows you to create a new wallet. Currently only Bitcoin Lightning wallets are supported.
Example request for creating a wallet POST /wallets
{
  "walletName": "New LN Wallet"
}
Example 201 CREATED  response for POST /wallets
{
  "data": {
    "id": "68a560f0-495b-4bfc-843a-fce7baba767d",
    "name": "New LN Wallet",
    "withdrawalAddressTimeLockInMillis": 259200000,
    "assets": [
      {
        "assetType": "BTC_LN",
        "assetName": "Bitcoin Lightning Network",
        "assetDisplayName": "Satoshis",
        "balance": "0.0",
        "depositAddress": "bc1qgqfeney9c0m33fukrhxr2r8yy9mz7wgrt7fsa4"
      }
    ],
    "withdrawalAddresses": []
  },
  "metadata": {}
}
HTTP REQUEST
POST /wallets
REQUEST BODY
Field
Type
Description
Validation rules
walletName
String
Human readable name for the wallet
required
HTTP RESPONSE
201 CREATED
The endpoint returns a Wallet
Submit withdrawal address
Example request for submitting a withdrawal address at POST /wallets/: walletId/withdrawal-addresses
{
  "label": "My Ether Wallet",
  "destinationAddress": "0x1234567890abcdef1234567890abcdef12345678",
  "assetType": "ETH",
  "beneficiary": {
    "type": "LEGAL",
    "name": "Lorem Ipsum",
    "vaspName": "Januar aps",
    "walletType": "CUSTODIAL"
  }
}
Example 201 Created  response from submit withdrawal address
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "walletId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "label": "My Ether Wallet",
  "initiated": "2023-03-20T12:39:44.177Z",
  "validFrom": null,


---

## Page 22

  "destinationAddress": "0x1234567890abcdef1234567890abcdef12345678",
  "assetType": "ETH",
  "status": "INITIATED",
  "beneficiary": {
    "type": "LEGAL",
    "name": "Lorem Ipsum",
    "vaspName": "Januar aps",
    "walletType": "CUSTODIAL"
  }
}
This endpoint allows you to submit a withdrawal address for a given wallet.
NOTE: When a withdrawal address is submitted, it will be in the INITIATED  state. The withdrawal address will be activated after a certain time period, which is determined by the wi
thdrawalAddressTimeLockInMillis  property of the wallet. The withdrawal address will be activated at the validFrom  timestamp. This is a security measure to prevent compromised
customers from submitting a withdrawal address to an attacker, and thus instantly being able to withdraw funds.
HTTP REQUEST
POST /wallets/:walletId/withdrawal-addresses
PATH PARAMETERS
Parameter
Type
Description
walletId
UUID
ID of wallet to add and submit withdrawal address for
REQUEST BODY
Parameter
Type
Description
Validation rules
label
String
Label for withdrawal address
required
destinationAddress
String
Destination address to withdraw to
required
assetType
AssetType
Asset type of the withdrawal address.
required
beneficiary
CryptoBeneficiary
Beneficiary details for travel rule compliance.
required
HTTP RESPONSE
The endpoint returns a withdrawal address object.
POSSIBLE ERRORS
HTTP Status code
Error Code
Description
context
400 Bad Request
VALIDATION
Request body had invalid input
context  contains a list of validation errors
400 Bad Request
CRYPTO_UNSUPPORTED_ASSET_TYPE
The given asset type is not supported
assetType  with the submitted unsupported crypto assetType
400 Bad Request
CRYPTO_WITHDRAWAL_ADDRESS_DUPLICATE
A withdrawal address with the same label already exists
label  with the submitted withdrawal address label
400 Bad Request
CRYPTO_INVALID_ETH_ADDRESS
The given Ethereum address is invalid
address  with the submitted Ethereum address
400 Bad Request
CRYPTO_INVALID_BTC_ADDRESS
The given Bitcoin address is invalid
address  with the submitted Bitcoin address
404 Not Found
CRYPTO_WALLET_NOT_FOUND
The given wallet was not found
walletId  with the submitted wallet ID
Update travel rule details for withdrawal address
{
  "beneficiary": {
    "type": "NATURAL",
    "name": "Lorem Ipsum",
    "vaspName": "Januar aps",
    "walletType": "UNKNOWN"
  }
}
Example 201 Created  response from submit withdrawal address
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "walletId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "label": "My Ether Wallet",
  "initiated": "2023-03-20T12:39:44.177Z",
  "validFrom": null,
  "destinationAddress": "0x1234567890abcdef1234567890abcdef12345678",
  "assetType": "ETH",
  "status": "INITIATED",
  "beneficiary": {
    "type": "NATURAL",
    "name": "Lorem Ipsum",
    "vaspName": "Januar aps",
    "walletType": "UNKNOWN"


---

## Page 23

  }
}
This endpoint allows you to update the travel rule details for a withdrawal address.
HTTP REQUEST
PUT /wallets/:walletId/withdrawal-addresses/:withdrawaladdressId
PATH PARAMETERS
Parameter
Type
Description
walletId
UUID
ID of wallet owning the withdrawal address
withdrawaladdressId
UUID
ID of withdrawal addressto update
REQUEST BODY
Parameter
Type
Description
Validation rules
beneficiary
CryptoBeneficiary
Beneficiary details for travel rule compliance.
required
HTTP RESPONSE
The endpoint returns a withdrawal address object.
Delete withdrawal address
Example 204 No Content  response for DELETE /wallets/:walletId/withdrawal-addresses/:withdrawalAddressId
This endpoint allows you to delete a withdrawal address for a given wallet.
HTTP REQUEST
DELETE /wallets/:walletId/withdrawal-addresses/:withdrawalAddressId
PATH PARAMETERS
Parameter
Type
Description
walletId
UUID
ID of wallet to submit withdrawal for
withdrawalAddressId
UUID
ID of withdrawal address to delete
HTTP RESPONSE
The endpoint returns a 204 No Content  response with an empty body.
POSSIBLE ERRORS
HTTP Status code
Error Code
Description
context
404 Not Found
CRYPTO_WALLET_NOT_FOUND
The given wallet was not found
walletId  with the submitted wallet ID
404 Not Found
CRYPTO_WITHDRAWAL_ADDRESS_NOT_FOUND
The given withdrawal address was not found
withdrawalAddressId  with the submitted withdrawal address ID
List crypto transactions
This endpoint returns a paged list of all transactions for a given wallet.
Example 200 OK  response for GET /wallets/:walletId/transactions
{
  "data": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "type": "CRYPTOTRANSACTION",
      "walletId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "direction": "OUTGOING",
      "destinationAddress": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "sourceAddress": "0x1234567890abcdef",
      "assetType": "ETH",
      "amount": "0.1",
      "amountEUR": "1000.34",
      "networkFee": "0.0001",
      "estimatedNetworkFee": "0.0001",
      "feeAssetType": "ETH",
      "status": "PENDING",
      "note": "Payment for services",
      "blockHeight": 123456,
      "blockchainTxHash": "0x1234567890abcdef",
      "created": "2021-01-01T00:00:00Z"
    }
  ],
  "metadata": {
    "pagination": {


---

## Page 24

      "pageSize": 1000,
      "page": 0,
      "totalRecords": 1
    }
  }
}
HTTP REQUEST
GET /wallets/:walletId/transactions
PATH PARAMETERS
Parameter
Description
walletId
ID of wallet to list crypto transactions for
QUERY PARAMETERS
Parameter
Default
Description
pageSize
100
Positive integer determining how many transactions to return per page, max 1000
page
0
Page number to retrieve, 0-indexed
statuses
[]
List of CryptoTransactionStatus to query. If not provided, all types will be queried
dateFrom
null
Determines the earliest transactionTime of the transactions queried. Format YYYY-MM-DD
dateTo
null
Determines the latest transactionTime of the transactions queried. Format YYYY-MM-DD
amountFrom
null
Determines the inclusive lower limit for the transaction amount
amountTo
null
Determines the inclusive upper limit for the transaction amount
assetTypes
[]
List of assetTypes code to query. If not provided, all transaction assetTypes will be queried
text
null
Search term. Will query in following fields note , destinationAddress , sourceAddress
direction
null
Transaction direction, INGOING or OUTGOING
HTTP RESPONSE
200 OK
The endpoint returns a list of crypto transaction (including Bolt11 crypto transactions).
POSSIBLE ERRORS
HTTP Status Code
Error Code
Description
context
404 Not Found
CRYPTO_WALLET_NOT_FOUND
The wallet with the given ID does not exist.
walletId
400 Bad Request
VALIDATION
Some of the input is invalid. For example :page  or :pageSize  being too small
The invalid fields and the submitted values
Get crypto transaction
This endpoint returns a transaction for a given wallet.
Example 200 OK  response for GET /wallets/:walletId/transactions/:transactionId
{
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "type": "CRYPTOTRANSACTION",
    "walletId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "direction": "OUTGOING",
    "destinationAddress": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "sourceAddress": "0x1234567890abcdef",
    "assetType": "ETH",
    "amount": "0.1",
    "amountEUR": "1000.34",
    "networkFee": "0.0001",
    "estimatedNetworkFee": "0.0001",
    "feeAssetType": "ETH",
    "status": "PENDING",
    "note": "Payment for services",
    "blockHeight": 123456,
    "blockchainTxHash": "0x1234567890abcdef",
    "created": "2021-01-01T00:00:00Z"
  },
  "metadata": {}
}
HTTP REQUEST
GET /wallets/:walletId/transactions/:transactionId
PATH PARAMETERS


---

## Page 25

Parameter
Description
walletId
ID of wallet to get the transaction
transactionId
ID of transaction to be viewed
HTTP RESPONSE
200 OK
The endpoint returns a crypto transaction (or Bolt11 Crypto transaction).
POSSIBLE ERRORS
HTTP Status Code
Error Code
Description
context
404 Not Found
CRYPTO_WALLET_NOT_FOUND
The wallet with the given ID does not exist.
walletId
404 Not Found
CRYPTOTRANSACTION_NOT_FOUND
The transaction with the given ID does not exist.
transactionId
Initiate crypto withdrawal
This endpoint allows you to initiate a crypto withdrawal from a given wallet.
Example request for initiating a crypto withdrawal POST /wallets/:walletId/transactions
{
  "amount": 0.1,
  "assetType": "ETH",
  "withdrawalAddressId": "d81b63a2-efe2-4aee-abbf-a978f2037043",
  "note": "Payment for services",
  "replayId" : "ETH9ec956e1-e236-4f31-b7be-4feacaf4089b"
}
Example 201 CREATED  response for POST /wallets/:walletId/transactions
{
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "type": "CRYPTOTRANSACTION",
    "walletId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "direction": "OUTGOING",
    "destinationAddress": "d81b63a2-efe2-4aee-abbf-a978f2037043",
    "sourceAddress": "0x1234567890abcdef",
    "assetType": "ETH",
    "amount": "0.1",
    "amountEUR": "1000.34",
    "networkFee": "0.0001",
    "estimatedNetworkFee": "0.0001",
    "feeAssetType": "ETH",
    "status": "INITIATED",
    "note": "Payment for services",
    "blockHeight": null,
    "blockchainTxHash": null,
    "created": "2021-01-01T00:00:00Z"
  },
  "metadata": {}
}
HTTP REQUEST
POST /wallets/:walletId/transactions
PATH PARAMETERS
Parameter
Type
Description
walletId
UUID
ID of wallet to initiate crypto withdrawal for
REQUEST BODY
Field
Type
Description
Validation rules
amount
Long
Amount of crypto to withdraw
required , positive
assetType
AssetType
Type of crypto to withdraw
required
withdrawalAddressId
UUID
ID of withdrawal address to withdraw to
required
note
String
Internal note to attach to the withdrawal
None
replayId
String
A unique id to help avoid duplicate withdrawal
None
HTTP RESPONSE
201 CREATED
The endpoint returns the crypto transaction that was initiated.


---

## Page 26

POSSIBLE ERRORS
HTTP
Status
Code
Error Code
Description
context
404 Not Fo
und
CRYPTO_WALLET_NOT_FOUND
The wallet with the given ID does
not exist.
walletId  with the submitted wallet ID
404 Not Fo
und
CRYPTO_WITHDRAWAL_ADDRE
SS_NOT_FOUND
The withdrawal address with the
given ID does not exist.
withdrawalAddressId  with the submitted withdrawal address ID
400 Bad Re
quest
VALIDATION
Some of the input is invalid. For
example :amount  being negative
The invalid fields and the submitted values
400 Bad Re
quest
CRYPTOTRANSACTION_INSUF
FICIENT_BALANCE
The wallet does not have enough
balance to withdraw the amount
balance  of the given asset, amount  with the submitted amount, estimatedFee  with the estimated fee
from the provider, total  = amount  + estimatedFee  which the asset balance  needs to hold to initiate
the crypto transaction
400 Bad Re
quest
CRYPTOTRANSACTION_INCOR
RECT_WITHDRAWAL_ASSET_TY
PE
Transaction and withdrawal
address asset types does not
match
transaction.assetType  with the submitted asset type, withdrawalAddress.assetType  with the
withdrawal address asset type
400 Bad Re
quest
CRYPTOTRANSACTION_WITHD
RAWAL_ADDRESS_NOT_ACTIV
E
The withdrawal address is not
active
withdrawalAddress.id  with the submitted withdrawal address ID, withdrawalAddress.status  with the
withdrawal address status
Confirm withdrawal
This endpoint allows you to confirm a withdrawal that was initiated.
Example request for confirming a withdrawal PUT /wallets/:walletId/transactions/: transactionId/confirm
{}
Example 200 OK  response for PUT /wallets/:walletId/transactions/:transactionId/confirm
{
  "data": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "type": "CRYPTOTRANSACTION",
    "walletId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "direction": "OUTGOING",
    "destinationAddress": "d81b63a2-efe2-4aee-abbf-a978f2037043",
    "sourceAddress": "0x1234567890abcdef",
    "assetType": "ETH",
    "amount": "0.1",
    "amountEUR": "1000.34",
    "networkFee": "0.0001",
    "estimatedNetworkFee": "0.0001",
    "feeAssetType": "ETH",
    "status": "CONFIRMED",
    "note": "Payment for services",
    "blockHeight": null,
    "blockchainTxHash": null,
    "created": "2021-01-01T00:00:00Z"
  },
  "metadata": {}
}
HTTP REQUEST
PUT /wallets/:walletId/transactions/:transactionId/confirm
PATH PARAMETERS
Parameter
Type
Description
walletId
UUID
ID of wallet to confirm crypto withdrawal for
transactionId
UUID
ID of crypto transaction to confirm withdrawal
REQUEST BODY
This endpoint does not accept a request body.
HTTP RESPONSE
200 OK
The endpoint returns the crypto transaction that was confirmed.
POSSIBLE ERRORS


---

## Page 27

HTTP
Status
Code
Error Code
Description
context
404 Not Fo
und
CRYPTO_WALLET_NOT_FOUN
D
The wallet with the given ID does
not exist.
walletId  with the submitted wallet ID
404 Not Fo
und
CRYPTO_TRANSACTION_NOT_
FOUND
The transaction with the given ID
does not exist.
transactionId  with the submitted transaction ID
400 Bad Re
quest
CRYPTO_TRANSACTION_ALRE
ADY_PROCESSED
The transaction has already been
confirmed and processed.
transactionId  with the submitted transaction ID
400 Bad Re
quest
CRYPTOTRANSACTION_WITHD
RAWAL_ADDRESS_NOT_ACTIV
E
The withdrawal address is not
active
withdrawalAddress.id  with the submitted withdrawal address ID, withdrawalAddress.status  with the
withdrawal address status
400 Bad Re
quest
CRYPTOTRANSACTION_INSUF
FICIENT_BALANCE
The wallet does not have enough
balance to withdraw the amount
balance  of the given asset, amount  with the submitted amount, estimatedFee  with the estimated fee
from the provider, total  = amount  + estimatedFee  which the asset balance  needs to hold to initiate
the crypto transaction
Bitcoin Lightning and bolt11 memos
Due to GDPR concerns, only a well-formatted SHA1 hash allowed in the memo field of a bolt11 invoice. This is to ensure that no personal data is included in the memo, which could
otherwise lead to GDPR violations. Applies to both in- and outgoing transactions.
Create Bolt11 invoice - Bitcoin Lightning
This endpoint allows you to create a bolt11 invoice for a given Lightning wallet, thus enabling you to receive bitcoin (satoshis)
Example request for creating a bolt11 invoice POST /wallets/:walletId/transactions/bolt11/create
{
  "amount": "21",
  "memo": "37de7433db93c025a175cc1417dcada8fff85366"
}
Example 201 CREATED  response for POST /wallets/:walletId/transactionsbolt/bolt11/create
{
  "data": {
    "id": "354f38f6-2a70-4e4b-b698-53de3a25d11b",
    "type": "BOLT11CRYPTOTRANSACTION",
    "walletId": "621c61e1-384a-4f93-bccf-e4ecf9c9dd59",
    "direction": "INGOING",
    "assetType": "BTC_LN",
    "amount": "21.0",
    "amountEUR": "0.00",
    "networkFee": "0.0",
    "feeAssetType": "BTC_LN",
    "status": "INITIATED",
    "created": "2025-03-27T13:17:33.007826Z",
    "januarTransactionFee": "0.0",
    "bolt11Status": "OPEN",
    "invoiceExpires": "2025-03-27T13:32:32Z",
    "bolt11Invoice": "lnbc220n1pn72nlvp....qqlftspn4t95q",
    "memo": "37de7433db93c025a175cc1417dcada8fff85366"
  },
  "metadata": {}
}
HTTP REQUEST
POST /wallets/:walletId/transactions/bolt11/create
PATH PARAMETERS
Parameter
Type
Description
walletId
UUID
ID of wallet to receive funds
REQUEST BODY
Field
Type
Description
Validation rules
amount
Long
Amount satoshis
required , positive
memo
UUID
Memo to send in the invoice
Well-formatted sha1, "37de7433db93c025a175cc1417dcada8fff85366"
HTTP RESPONSE
201 CREATED
The endpoint returns a bolt11 crypto transaction that was initiated, including the bolt11 invoice.


---

## Page 28

POSSIBLE ERRORS
HTTP
Status
Code
Error Code
Description
context
404 Not Fou
nd
CRYPTO_WALLET_NOT_F
OUND
The wallet with the given ID does
not exist.
walletId  with the submitted wallet ID
400 Bad Req
uest
VALIDATION
Some of the input is invalid. For
example :amount  being negative
The invalid fields and the submitted values
400 Bad Req
uest
CRYPTOTRANSACTION_I
NSUFFICIENT_BALANCE
The wallet does not have enough
balance to withdraw the amount
balance  of the given asset, amount  with the submitted amount, estimatedFee  with the estimated fee from
the provider, total  = amount  + estimatedFee  which the asset balance  needs to hold to initiate the
crypto transaction
Decode Bolt11 invoice - Bitcoin Lightning
This endpoint allows you to decode a bolt11 invoice, inspecting the payment details
Example request to decode a bolt11 invoice POST /wallets/:walletId/transactions/bolt11/decode
{
  "bolt11Invoice": "lnbc280n1pnagta3pp5exckw6f...."
}
Example 200 OK  response for POST /wallets/:walletId/transactions/bolt11/decode
{
  "data": {
    "bitcoinNetwork": "mainnet",
    "amount": 21,
    "timestamp": 1743081201,
    "expirationTime": 86400,
    "paymentHash": "5e3b6cb7e48c...5e91ae3f81e78da47d52479",
    "description": "Please pay 21 satoshis"
  },
  "metadata": {}
}
HTTP REQUEST
POST /wallets/:walletId/transactions/bolt11/decode
PATH PARAMETERS
Parameter
Type
Description
walletId
UUID
ID of lightning wallet
REQUEST BODY
Field
Type
Description
Validation rules
bolt11Invoice
String
Bolt 11 invoice
required
HTTP RESPONSE
200 OK
The endpoint returns the payment details for a given bolt11 invoice.
Initiate payment of Bolt11 invoice - Bitcoin Lightning
This endpoint allows you to initiate payment of a bolt11 invoice (must "confirm" after)
Example request for initiating a bolt11 payment POST /wallets/:walletId/transactions/bolt11/
{
  "bolt11Invoice": "lnbc280n1pnagta3pp5exckw6f....",
  "beneficiary": {
    "type": "NATURAL",
    "name": "Lorem Ipsum",
    "vaspName": "Januar aps",
    "walletType": "UNKNOWN"
  }
}
Example 201 CREATED  response for POST /wallets/:walletId/transactions/bolt11
{
  "data": {
    "id": "797588d4-45fa-4305-8439-1738eecf1656",


---

## Page 29

    "type": "BOLT11CRYPTOTRANSACTION",
    "walletId": "621c61e1-384a-4f93-bccf-e4ecf9c9dd59",
    "direction": "OUTGOING",
    "assetType": "BTC_LN",
    "amount": "1200.0",
    "amountEUR": "0.09",
    "networkFee": "",
    "feeAssetType": "BTC_LN",
    "status": "INITIATED",
    "created": "2025-03-27T13:14:00.583716Z",
    "januarTransactionFee": "0.01",
    "bolt11Status": "OPEN",
    "invoiceExpires": "2025-03-28T13:13:21Z",
    "bolt11Invoice": "lnbc280n1pnagta3pp5exckw6f....",
    "memo": ""
  },
  "metadata": {}
}
HTTP REQUEST
POST /wallets/:walletId/transactions/bolt11
PATH PARAMETERS
Parameter
Type
Description
walletId
UUID
ID of lightning wallet
REQUEST BODY
Field
Type
Description
Validation rules
bolt11Invoice
String
Bolt11 invoice
required
beneficiary
CryptoBeneficiary
Beneficiary details for travel rule compliance.
required
HTTP RESPONSE
201 CREATED
The endpoint returns the bolt11 crypto transaction that was initiated. Use the /confirm endpoint to confirm the transaction.
Confirm payment of Bolt11 invoice - Bitcoin Lightning
This endpoint allows you to confirm the payment of a bolt11 invoice (must be initiated first)
Example request for confirming payment of bolt11 POST /wallets/:walletId/transactions/bolt11/{bolt11CryptoTransactionId}/confirm
{}
Example 200 OK  response for POST /wallets/:walletId/transactions/bolt11/{bolt11CryptoTransactionId}/confirm
{
  "data": {
    "id": "797588d4-45fa-4305-8439-1738eecf1656",
    "type": "BOLT11CRYPTOTRANSACTION",
    "walletId": "621c61e1-384a-4f93-bccf-e4ecf9c9dd59",
    "direction": "OUTGOING",
    "assetType": "BTC_LN",
    "amount": "1200.0",
    "amountEUR": "0.09",
    "networkFee": "",
    "feeAssetType": "BTC_LN",
    "status": "CONFIRMING",
    "created": "2025-03-27T13:14:00.583716Z",
    "januarTransactionFee": "0.01",
    "bolt11Status": "IN_FLIGHT",
    "invoiceExpires": "2025-03-28T13:13:21Z",
    "bolt11Invoice": "lnbc280n1pnagta3pp5exckw6f....",
    "memo": "37de7433db93c025a175cc1417dcada8fff85366"
  },
  "metadata": {}
}
HTTP REQUEST
POST /wallets/:walletId/transactions/bolt11/{bolt11CryptoTransactionId}/confirm
PATH PARAMETERS
Parameter
Type
Description
walletId
UUID
ID of lightning wallet
bolt11CryptoTransactionId
UUID
ID of Bolt11 crypto transaction to confirm
REQUEST BODY
This endpoint does not accept a request body.


---

## Page 30

HTTP RESPONSE
200 OK
The endpoint returns the bolt11 crypto transaction that was confirmed.
POSSIBLE ERRORS
HTTP Status Code
Error Code
Description
404 Not Found
CRYPTO_WALLET_NOT_FOUND
The wallet with the given ID does not exist.
404 Not Found
CRYPTO_TRANSACTION_NOT_FOUND
The transaction with the given ID does not exist.
400 Bad Request
CRYPTO_TRANSACTION_ALREADY_PROCESSED
The transaction has already been confirmed and processed.
400 Bad Request
CRYPTOTRANSACTION_INSUFFICIENT_BALANCE
The wallet does not have enough balance to withdraw the amount
Crypto data model
This section describes the data model of each type of entity in the Crypto API:
Wallet
Crypto transaction
Bolt11 Crypto transaction
Withdrawal address
CryptoBeneficiary
WALLET
Example wallet object
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "My wallet",
  "assets": [
    {
      "assetType": "ETH",
      "balance": "0.1",
      "depositAddress": "0x1234567890"
    }
  ],
  "withdrawalAddressTimeLockInMillis": 259200,
  "withdrawalAddresses": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "walletId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "label": "My Ether Wallet",
      "initiated": "2023-03-20T12:39:44.177Z",
      "validFrom": "2023-03-20T12:39:44.177Z",
      "destinationAddress": "0x1234567890abcdef1234567890abcdef12345678",
      "assetType": "ETH",
      "status": "INITIATED"
    }
  ]
}
A wallet holds a collection of assets in one or more crypto-currencies and withdrawal addresses.
Field
Type
Description
id
UUID
The unique identifier of the wallet
name
String
The name of the wallet
assets
Assets
The list of assets in the wallet
↳ assetType
AssetType
assetType  describes the crypto currency shortname - eg. ETH .
↳ balance
String
balance  describes the amount of the asset in the wallet. See more on precision
↳ depositAddress
String
depositAddress  describes the address where the asset can be deposited.
withdrawalAddressTimeLockInMil
lis
Long
The time lock in milliseconds for withdrawal addresses. The time-lock is a time period from creation of a withdrawal till it
becomes active.
withdrawalAddresses
Withdrawal
Addresses
The list of withdrawal addresses
CRYPTO TRANSACTION
Example OUTGOING  crypto transaction
Note that some fields may be null depending on the transaction status. For example, blockHeight  and blockchainTxHash  can be null for a PENDING  transaction, because the
transaction may not have been broadcasted to the blockchain yet.
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "type": "CRYPTOTRANSACTION",
  "walletId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",


---

## Page 31

  "direction": "OUTGOING",
  "destinationAddress": "0x1234567890abcdef",
  "sourceAddress": "0x1234567890abcdef",
  "assetType": "ETH",
  "amount": "0.1",
  "amountEUR": "1000.34",
  "networkFee": "0.0001",
  "estimatedNetworkFee": "0.0001",
  "feeAssetType": "ETH",
  "status": "PENDING",
  "note": "Payment for services",
  "blockHeight": 123456,
  "blockchainTxHash": "0x1234567890abcdef",
  "created": "2021-01-01T00:00:00Z"
}
A crypto transaction represents a transfer of crypto assets between two addresses.
Field
Type
Description
id
UUID
The unique identifier of the crypto transaction
type
CryptoTransactionType
The type of the CryptoTransaction, ie "CRYPTOTRANSACTION"
walletId
UUID
The unique identifier of the wallet the transaction belongs to
direction
String
direction  describes the direction of the transaction. Possible values are INGOING  and OUTGOING
destinationAddress
String
destinationAddress  describes the destination address of the transaction.
sourceAddress
String
sourceAddress  describes the source address of the transaction.
assetType
AssetType
assetType  describes the crypto currency shortname - eg. ETH .
amount
String
amount  describes the amount of the asset in the transaction.
amountEUR
String
amountEUR  describes the amount of the asset in the transaction in EUR.
networkFee
String
networkFee  describes the network fee of the transaction.
estimatedNetworkFee
String
estimatedNetworkFee  describes the estimated network fee of the transaction.
feeAssetType
AssetType
feeAssetType  describes the crypto currency shortname - eg. ETH  - of the network fee.
status
CryptoTransactionStatus
status  describes the status of the transaction.
note
String
The note  field is an internal field only visible to you which can be used to describe what the transactions is for.
blockHeight
Long
blockHeight  describes the block height of the transaction.
blockchainTxHash
String
blockchainTxHash  describes the blockchain hash of the transaction. Can be used to look up transaction in a block explorer.
created
Date
The date when the transaction was created
BOLT11 CRYPTO TRANSACTION
Note that some fields may be null depending on the transaction status.
{
  "id": "797588d4-45fa-4305-8439-1738eecf1656",
  "type": "BOLT11CRYPTOTRANSACTION",
  "walletId": "621c61e1-384a-4f93-bccf-e4ecf9c9dd59",
  "direction": "OUTGOING",
  "assetType": "BTC_LN",
  "amount": "120.0",
  "amountEUR": "0.00",
  "networkFee": "",
  "feeAssetType": "BTC_LN",
  "status": "INITIATED",
  "created": "2025-03-27T13:14:00.583716Z",
  "januarTransactionFee": "0.01",
  "bolt11Status": "OPEN",
  "invoiceExpires": "2025-03-28T13:13:21Z",
  "bolt11Invoice": "lnbc1200n1pn72nh3pp5t...",
  "memo": "37de7433db93c025a175cc1417dcada8fff85366"
}
A bolt11 crypto transaction represents a transfer of satoshis on the Bitcoin Lightning network.
Field
Type
Description
id
UUID
The unique identifier of the crypto transaction
type
CryptoTransactionType
The type of the CryptoTransaction, ie "BOLT11CRYPTOTRANSACTION"
walletId
UUID
The unique identifier of the wallet the transaction belongs to
direction
String
direction  describes the direction of the transaction. Possible values are INGOING  and OUTGOING
assetType
AssetType
assetType  describes the crypto currency shortname. Always BTC_LN.


---

## Page 32

Field
Type
Description
amount
String
amount  describes the amount of the asset in the transaction.
amountEUR
String
amountEUR  describes the amount of the asset in the transaction in EUR.
networkFee
String
networkFee  describes the network fee of the transaction.
feeAssetType
AssetType
feeAssetType  describes the crypto currency shortname - eg. BTC_LN  - of the network fee.
status
CryptoTransactionStatus
status  describes the status of the transaction.
created
Date
The date when the transaction was created
januarTransactionFee
String
Januar transaction fee for the transaction, in EUR
bolt11Status
Bolt11Status
bolt11status  describes the status of the bolt11 invoice.
invoiceExpires
Date
The date when the bolt11 invoice will expire (default 900 seconds)
bolt11Invoice
String
The bolt11 invoice
memo
SHA1 hash, 40 chars hexadecimal
Memo sent along in the bolt11 payment
CRYPTO TRANSACTION TYPES
Type
Description
CRYPTOTRANSACTION
Standard crypto transaction
BOLT11CRYPTOTRANSACTION
Specific type for Bitcoin Lighting transactions based on bolt 11 invoices.
CRYPTO TRANSACTIONS STATUSES
Status
Description
INITIATED
The crypto transaction has just been created.
PENDING
The crypto transaction is waiting to be broadcasted to the blockchain.
CONFIRMING
The crypto transaction is on the blockchain and is being confirmed.
COMPLETED
The crypto transaction has been completed.
FAILED
The crypto transaction has failed.
BOLT11 STATUSES
Status
Description
OPEN
The invoice is created, but not paid.
IN_FLIGHT
The payment is being resolved.
SETTLED
The invoice is paid.
EXPIRED
The invoice have expired and can no longer be paid.
FAILED
The invoice have failed.
WITHDRAWAL ADDRESS
Example withdrawal address
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "walletId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "label": "My withdrawal address",
  "initiated": "2021-01-01T00:00:00Z",
  "validFrom": "2021-01-01T00:00:00Z",
  "destinationAddress": "0x1234567890abcdef",
  "assetType": "ETH",
  "status": "ACTIVE",
  "beneficiary": {
    "type": "NATURAL",
    "name": "John Doe",
    "vaspName": "Januar aps",
    "walletType": "NON_CUSTODIAL"
  }
}
A withdrawal address represents a destination address for crypto assets.
Field
Type
Description
id
UUID
The unique identifier of the withdrawal address
walletId
UUID
The unique identifier of the wallet the withdrawal address belongs to


---

## Page 33

Field
Type
Description
label
String
The unique label of the withdrawal address
initiated
Date
The date when the withdrawal address was created
validFrom
Date
The date when the withdrawal address became active
destinationAddress
String
The destination address of the withdrawal address
beneficiary
CryptoBeneficiary
Beneficiary details for travel rule compliance.
assetType
AssetType
assetType  describes the crypto currency shortname - eg. ETH .
status
WithdrawalAddressStatus
status  describes the status of the withdrawal address.
CRYPTOBENEFICIARY
Example CryptoBeneficiary object
{
  "beneficiary": {
    "type": "NATURAL",
    "name": "Lorem Ipsum",
    "vaspName": "Januar aps",
    "walletType": "UNKNOWN"
  }
}
Field
Type
Description
Validation Rules
type
BeneficiaryType
Type of beneficiary
required
name
String
The name of the beneficiary
required
vaspName
String
Name of the beneficiary VASP
walletType
WalletType
Type of wallet
required
BENEFICIARYTYPE
Type
UNKNOWN
NATURAL
LEGAL
WALLETTYPE
Wallet type
UNKNOWN
CUSTODIAL
NON_CUSTODIAL
WITHDRAWAL ADDRESS STATUSES
NOTE: Please contact us if you encounter a REMOVED_BY_THIRD_PARTY  status. This should never happen and Januar Support will investigate.


---

## Page 34

INITIATED
APPROVED
ACTIVE
REMOVED_BY_THIRD_PARTY
Crypto conversions
Crypto conversions allow you to convert between fiat and crypto assets. This feature is available upon request. Please contact your account manager for more information.
This section aims to provide a high-level overview of the different entities and concepts in the Crypto Conversion API
Concept
Description
FiatCrypto
A conversion from fiat to crypto, i.e. onramp (EUR->BTC)
CryptoFiat
A conversion from crypto to fiat, i.e. offramp (BTC->EUR)
Market order
A conversion using market liquidity. Index is executed once source assets are available at exchange provider - depending on asset this can take minutes or hours.
Shown price estimate can vary from executed price.
RFQ order
A conversion based on a specific price quote - estimated price will equal final executed price. Price qoutes are valid for 15 seconds,
Mint
A conversion based on minting / burning of directly at stablecoin provider
Transportation fees
Moving both crypto and fiat incurs fees (blockchain/gas fees, withdrawal fees etc). Transportation fees are outside the control of januar and are subtracted from
any final amounts traded.
Exchange Pair
A pair of assets - left side is sell, right side is buy
Settlement window
Daily window in which the service is not available
Mean settlement
time
Average time in seconds for a conversion to be settled. For RFQ order the conversion is executed immediately, but the settlement and transfer of assets in our
system may take longer.
Crypto conversion details
This endpoint returns all important details for the crypto conversion feature, i.e. assets, exchange pairs and service status. Please note our daily settlement window in which the service is not
available.
HTTP REQUEST
GET /wallets/:walletId/cryptoconversions/details
HTTP RESPONSE


---

## Page 35

200 OK
Example 200 OK  response
{
  "data": {
    "cryptoConversionAvailable": true,
    "reasonForClose": "",
    "settlementWindow": "22:00:00 - 00:00:00 UTC",
    "availableAssets": [
      {
        "assetType": "BTC",
        "assetName": "Bitcoin",
        "displayName": "BTC",
        "decimals": 8,
        "feeAssetType": "BTC",
        "feeAssetName": "Bitcoin testnet",
        "feeDecimals": 8
      },
      {
        "assetType": "USDC",
        "assetName": "USDC",
        "displayName": "USDC",
        "decimals": 6,
        "feeAssetType": "ETH",
        "feeAssetName": "Ethereum",
        "feeDecimals": 17
      },
      ....
    ],
    "availableExchangePairs": [
      {
        "exchangePair": "EURBTC",
        "sellAsset": "EUR",
        "buyAsset": "BTC",
        "orderType": "RFQ",
        "meanSettlementTime": 120.65
      },
      {
        "exchangePair": "EURETH",
        "sellAsset": "EUR",
        "buyAsset": "ETH",
        "orderType": "RFQ",
        "meanSettlementTime": 43.65
      },
      ...
    ]
  },
  "metadata": {}
}
Field
Type
Description
cryptoConversionAvailable
Boolean
Whether the crypto conversion feature is available.
reasonForClose
String
If cryptoConversionAvailable  is false, this field will contain the reason for the closure.
settlementWindow
String
The daily settlement window in which the service is not available.
availableAssets
Asset[]
List of available assets for crypto conversions.
- assetType
String
Asset type code.
- assetName
String
Asset name.
- displayName
String
Asset display name.
- decimals
Integer
Number of decimals for the asset.
- feeAssetType
String
Asset type code for fees.
- feeAssetName
String
Asset name for fees.
- feeDecimals
Integer
Number of decimals for the fee asset.
availableExchangePairs
ExchangePair[]
List of available exchange pairs for crypto conversions.
- exchangePair
String
Exchange pair code.
- sellAsset
String
Asset code for the sell side of the exchange pair.
- buyAsset
String
Asset code for the buy side of the exchange pair.
- orderType
String
Order type for the exchange pair.
- meanSettlementTime
Float
Mean settlement time in seconds for the exchange pair.
Initiate crypto conversion
This endpoint allows you to initiate a crypto conversion from a given wallet.


---

## Page 36

Example request for initiating a crypto conversion POST /wallets/: walletId/cryptoconversions/initialise
{
  "fromAsset": "EUR",
  "toAsset": "BTC",
  "fromAmount": 300.23,
  "source": "b3f4867e-d1b0-43ac-a0ec-902e848a8d77",
  "destination": "a2a39665-466b-4cda-a920-b00ed2c20a3e"
}
Example 201 CREATED  response for POST /wallets/a2a39665-466b-4cda-a920-b00ed2c20a3e/cryptoconversions/initialise
{
  "data": {
    "id": "18c51736-a706-4e51-a0d2-2bf759b0ca03",
    "created": "2024-11-22T13:20:44.237765Z",
    "cryptoConversionType": "FIATCRYPTO",
    "cryptoConversionOrderType": "MARKET",
    "status": "INITIATED",
    "rate": null,
    "fromAmount": "200.00",
    "toAmount": "0.05289741023064255",
    "blockchainFee": null,
    "blockchainFeeAssetName": "ETH_TEST5",
    "estimatedBlockchainFee": "0.000703467460983",
    "estimatedRate": "0.000284226562677641602",
    "source": "2a439c0c-1a3b-4858-bbb9-acd7518cd2f3",
    "destination": "dcd272e5-3696-4182-8620-935aa175a597",
    "sourceName": "Trading account",
    "destinationName": "Crypto Account 1",
    "fromTransaction": null,
    "toTransaction": null,
    "sellAsset": "EUR",
    "buyAsset": "ETH_TEST5",
    "rfqInitiated": null,
    "rfqExpire": null
  },
  "metadata": {}
}
HTTP REQUEST
POST /wallets/:walletId/cryptoconversions/initialise
PATH PARAMETERS
Parameter
Type
Description
walletId
UUID
ID of wallet to initiate crypto conversion for
REQUEST BODY
Field
Type
Description
Validation rules
amount
String
Amount of crypto to withdraw
required , positive
fromAsset
String
Source asset or currency name
required
toAsset
String
Destination asset or currency name
required
source
UUID
Id of source wallet or account
required
destination
UUID
Id of destination wallet or account
required
HTTP RESPONSE
201 CREATED
The endpoint returns the crypto conversion that was initiated.
Confirm Crypto conversion
This endpoint allows you to confirm a crypto conversion that was initiated. For RFQ conversions, this must be done before the "rfqexpire" timestamp.
Example 200 OK  response for PUT /wallets/:walletId/cryptoconversions/:cryptoConversionId/confirm
{
  "data": {
    "id": "18c51736-a706-4e51-a0d2-2bf759b0ca03",
    "created": "2024-11-22T13:20:44.237765Z",
    "cryptoConversionType": "FIATCRYPTO",
    "cryptoConversionOrderType": "MARKET",
    "status": "CONFIRMED",
    "rate": null,
    "fromAmount": "200.00",
    "toAmount": "0.05276346612600555",
    "blockchainFee": null,
    "blockchainFeeAssetName": "ETH_TEST5",
    "estimatedBlockchainFee": "0.00083741156562",
    "estimatedRate": "0.000284226562677641602",


---

## Page 37

    "source": "2a439c0c-1a3b-4858-bbb9-acd7518cd2f3",
    "destination": "dcd272e5-3696-4182-8620-935aa175a597",
    "sourceName": "Trading account",
    "destinationName": "Crypto Account 1",
    "fromTransaction": null,
    "toTransaction": null,
    "sellAsset": "EUR",
    "buyAsset": "ETH_TEST5",
    "rfqInitiated": null,
    "rfqExpire": null
  },
  "metadata": {}
}
HTTP REQUEST
PUT /wallets/:walletId/cryptoconversions/:cryptoConversionId/confirm
PATH PARAMETERS
Parameter
Type
Description
walletId
UUID
ID of wallet to confirm crypto conversion for
cryptoConversionId
UUID
ID of crypto conversion to confirm
REQUEST BODY
This endpoint does not accept a request body.
HTTP RESPONSE
200 OK
The endpoint returns the crypto conversion that was confirmed.
POSSIBLE ERRORS
HTTP Status code
Error Code
Description
context
400 Bad Request
CRYPTO_CONVERSION_RFQ_EXPIRED
RFQ expired, please request a new
400 Bad Request
CRYPTO_CONVERSION_UNEXPECTED_STATUS
Index not waiting for confirmation
List crypto conversions
This endpoint returns a paged list of all crypto conversions for a given wallet.
Example 200 OK  response
for GET /wallets/a2a39665-466b-4cda-a920-b00ed2c20a3e/cryptoconversions/?page=0&pageSize=200&toAmountMin=300&dateFrom=2024-01-27&assetTypes=TRX
{
  "data": [
    {
      "id": "d510f906-358e-4999-b8dc-d4e592331593",
      "created": "2024-11-21T13:42:31.464831Z",
      "cryptoConversionType": "FIATCRYPTO",
      "cryptoConversionOrderType": "MARKET",
      "status": "COMPLETED",
      "rate": "30000.0000000000",
      "fromAmount": "200.00",
      "toAmount": "0.00573384",
      "blockchainFee": "0.00050616",
      "blockchainFeeAssetName": "BTC_TEST",
      "estimatedBlockchainFee": "0.00047799",
      "estimatedRate": "0.0000159949",
      "source": "2a439c0c-1a3b-4858-bbb9-acd7518cd2f3",
      "destination": "dcd272e5-3696-4182-8620-935aa175a597",
      "sourceName": "Trading account",
      "destinationName": "Crypto Account 1",
      "fromTransaction": "89bef7ad-e67c-40a7-89a3-a035c7ed0d11",
      "toTransaction": "2d088649-2b98-4a5e-b4d4-aa1787b52174",
      "sellAsset": "EUR",
      "buyAsset": "BTC_TEST",
      "rfqInitiated": null,
      "rfqExpire": null
    },
    ...
  ],
  "metadata": {
    "pagination": {
      "pageSize": 200,
      "page": 0,
      "totalRecords": 19
    }
  }
}
HTTP REQUEST
GET /wallets/:walletId/cryptoconversions/


---

## Page 38

PATH PARAMETERS
Parameter
Description
walletId
ID of wallet to list crypto conversions for specific wallet
QUERY PARAMETERS
Parameter
Default
Description
pageSize
100
Positive integer determining how many crypto conversions to return per page, max 1000
page
0
Page number to retrieve, 0-indexed
dateFrom
null
Determines the earliest created of the crypto conversions queried. Format YYYY-MM-DD
dateTo
null
Determines the latest created of the crypto conversions queried. Format YYYY-MM-DD
fromAmountMin
null
Determines the inclusive lower limit for the crypto conversions fromAmount
fromAmountMax
null
Determines the inclusive upper limit for the crypto conversions fromAmount
toAmountMin
null
Determines the inclusive lower limit for the crypto conversions toAmount
toAmountMax
null
Determines the inclusive upper limit for the crypto conversions toAmount
statuses
[]
List of CryptoConversionStatus to query. If not provided, all statuses will be queried
assetTypes
[]
List of assetTypes code to query. If not provided, all crypto conversion assetTypes will be queried
currencies
[]
List of currencies code to query. If not provided, all crypto conversion currencies will be queried
HTTP RESPONSE
200 OK
The endpoint returns a list of crypto conversion s.
Get crypto conversion
This endpoint returns a specific crypto conversion.
Example 200 OK  response for GET /a2a39665-466b-4cda-a920-b00ed2c20a3e/cryptoconversions/0cb05bf2-36eb-4f11-b01f-1397f40e74b1/
{
  "data": {
    "id": "d510f906-358e-4999-b8dc-d4e592331593",
    "created": "2024-11-21T13:42:31.464831Z",
    "cryptoConversionType": "FIATCRYPTO",
    "cryptoConversionOrderType": "MARKET",
    "status": "COMPLETED",
    "rate": "30000.0000000000",
    "fromAmount": "200.00",
    "toAmount": "0.00573384",
    "blockchainFee": "0.00050616",
    "blockchainFeeAssetName": "BTC_TEST",
    "estimatedBlockchainFee": "0.00047799",
    "estimatedRate": "0.0000159949",
    "source": "2a439c0c-1a3b-4858-bbb9-acd7518cd2f3",
    "destination": "dcd272e5-3696-4182-8620-935aa175a597",
    "sourceName": "Trading account",
    "destinationName": "Crypto Account 1",
    "fromTransaction": "89bef7ad-e67c-40a7-89a3-a035c7ed0d11",
    "toTransaction": "2d088649-2b98-4a5e-b4d4-aa1787b52174",
    "sellAsset": "EUR",
    "buyAsset": "BTC_TEST",
    "rfqInitiated": null,
    "rfqExpire": null
  },
  "metadata": {}
}
HTTP REQUEST
GET /:walletId/cryptoconversions/:cryptoConversionId/
HTTP RESPONSE
The endpoint returns a crypto conversion.
Index data model
This section describes the data model of each type of entity in the Index API:
CRYPTO CONVERSION
Example crypto conversion


---

## Page 39

Note that some fields may be null depending on the conversion status.
{
  "data": {
    "id": "d510f906-358e-4999-b8dc-d4e592331593",
    "created": "2024-11-21T13:42:31.464831Z",
    "cryptoConversionType": "FIATCRYPTO",
    "cryptoConversionOrderType": "MARKET",
    "status": "COMPLETED",
    "rate": "30000.0000000000",
    "fromAmount": "200.00",
    "toAmount": "0.00573384",
    "blockchainFee": "0.00050616",
    "blockchainFeeAssetName": "BTC_TEST",
    "estimatedBlockchainFee": "0.00047799",
    "estimatedRate": "0.0000159949",
    "source": "2a439c0c-1a3b-4858-bbb9-acd7518cd2f3",
    "destination": "dcd272e5-3696-4182-8620-935aa175a597",
    "sourceName": "Trading account",
    "destinationName": "Crypto Account 1",
    "fromTransaction": "89bef7ad-e67c-40a7-89a3-a035c7ed0d11",
    "toTransaction": "2d088649-2b98-4a5e-b4d4-aa1787b52174",
    "sellAsset": "EUR",
    "buyAsset": "BTC_TEST",
    "rfqInitiated": null,
    "rfqExpire": null
  },
  "metadata": {}
}
Field
Type
Description
id
UUID
The unique identifier of the crypto conversion
cryptoConversionType
String
FIATCRYPTO or CRYPTOFIAT
cryptoConversionOrderType
String
MARKET or RFQ or MINT
status
CryptoConversionStatus
status  describes the current status of the conversion.
estimatedRate
String
Estimated exchange rate before confirming trade.
rate
String
Final exchange rate.
fromAmount
String
Amount in source asset to be converted
toAmount
String
Final amount in destination asset
blockchainFee
String
Final amount paid in blockchain / gas fees
blockchainFeeAssetName
String
Asset of blockchain fee
estimatedBlockchainFee
String
Pre-confirm estimate of blockchain fee
source
UUID
Id of source wallet or account
source name
String
Name of source wallet or account
destination
UUID
Id of destination wallet or account
destination name
String
Name of destination wallet or account
fromTransaction
UUID
ID of OUTGOING transaction or crypto-transaction from the source
toTransaction
UUID
ID of INGOING transaction or crypto-transaction to the destination
sellAsset
String
Name of currency or crypto asset being sold
buyAsset
String
Name of currency or crypto asset being bought
rfqinitiated
String
Only for RFQ cryptoConversionOrderType: Quote valid from this timestamp
rfqexpire
String
Only for RFQ cryptoConversionOrderType: Quote expires at this timestamp - must be CONFIRMED before
CRYPTO CONVERSION STATUSES
Status
Description
INITIATED
The crypto conversion has just been created.
CONFIRMED
The crypto conversion have been confirmed and will be executed.
PENDING
The crypto conversion is being excuted / settled.
COMPLETED
The crypto conversion has been completed.
FAILED
The crypto conversion has failed.


---

## Page 40

Notifications
Terminology for notifications
This section aims to provide a high-level overview of the different entities and concepts for notifications
The overall concept of notifications is to subscribe to get updates on specific events. The triggering events are defined below under Available Channels. This platform currently supports
notifications via webhooks or email. To enable notifications, simply create a new notification via the Post Notifications endpoint. To disable notifications, simply delete any existing
notifications.
Concept
Description
Webhook
A Webhook is a HTTP POST initiated from januar to the given endpoint carrying a payload of data.
Email
An Email is a simple email containing relevant info regarding the triggering event from.
Channel
A Channel is the entity on which to subscribe to a given available notification. See list of available channels below.
Destination
A Destination is either an HTTP endpoint for Webhooks or an email address for Emails
Label
A Label is simply a human readable label for any given notification
Available Channels and destination types:
Channel
Destination type
Description
WEBHOOK_FIAT_ALL
A HTTP endpint
Subscribes to all updates on FIAT transactions, ie everytime a FIAT transaction changes state, a webhook is
triggered.
WEBHOOK_CRYPTO_ALL
A HTTP endpint
Subscribes to all updates on CRYPTO transactions, ie everytime a CRYPTO transaction changes state, a
webhook is triggered.
WITHDRAWAL_ADDRESS_UPDATE_EMAIL
A valid email
address
Sends an email to the given email address when any Crypto Withdrawal Address is initiated, confirmed or
cancelled.
CRYPTOCONVERSION_STATUS_EMAIL
A valid email
address
Sends an email to the given email address when any CryptoConversions are updated.
List notifications
Example 200 OK  response for GET /notifications
{
  "data": [
    {
      "id": "b7acbf16-7c23-4ef9-89c9-c1223dfe9a17",
      "channel": "WITHDRAWAL_ADDRESS_UPDATE_EMAIL",
      "destination": "test@test.com",
      "label": "label"
    }
  ],
  "metadata": {}
}
This endpoint returns a list of active notifications.
HTTP REQUEST
GET /notifications
HTTP RESPONSE
The endpoint returns a list of notification objects.
create notification
Example request for submitting a new notification at POST /notifications
{
  "channel":"WITHDRAWAL_ADDRESS_UPDATE_EMAIL",
  "destination":"test@test.com",
  "label":"label"
}
Example 201 Created  response from submit notification


---

## Page 41

{
  "data": [
    {
      "id": "b7acbf16-7c23-4ef9-89c9-c1223dfe9a17",
      "channel": "WEBHOOK_FIAT_ALL",
      "destination": "https://test.com/webhook",
      "label": "label"
    }
  ],
  "metadata": {}
}
This endpoints allows you to submit a new notification.
HTTP REQUEST
POST /notifications
REQUEST BODY
Parameter
Type
Description
Validation rules
channel
String
Channel, see available list above
required
destination
String
email or endpoint
required
label
String
Human readable label
required
HTTP RESPONSE
The endpoint returns a notification object.
POSSIBLE ERRORS
HTTP Status code
Error Code
Description
context
400 Bad Request
VALIDATION
Request body had invalid input
400 Bad Request
NOTIFICATION_INVALID
The destination is already defined
update notification
Example request for submitting a new notification at PUT /notifications/:notificationid
{
  "channel":"WITHDRAWAL_ADDRESS_UPDATE_EMAIL",
  "destination":"test@test.com",
  "label":"label"
}
Example 201 Created  response from submit notification
{
  "data": [
    {
      "id": "b7acbf16-7c23-4ef9-89c9-c1223dfe9a17",
      "channel": "WITHDRAWAL_ADDRESS_UPDATE_EMAIL",
      "destination": "test@test.com",
      "label": "label"
    }
  ],
  "metadata": {}
}
This endpoints allows you to update an existing notification.
HTTP REQUEST
PUT /notifications/:notificationid
PATH PARAMETERS
Parameter
Type
Description
notificationid
UUID
ID of notification to be updated
REQUEST BODY
Parameter
Type
Description
Validation rules
channel
String
Channel, see available list above
required
destination
String
email or endpoint
required
label
String
Human readable label
required
HTTP RESPONSE


---

## Page 42

The endpoint returns a notification object.
POSSIBLE ERRORS
HTTP Status code
Error Code
Description
context
400 Bad Request
VALIDATION
Request body had invalid input
400 Bad Request
NOTIFICATION_NOT_FOUND
The notification can not be found
Delete notification
This endpoint allows you to delete a given notification.
HTTP REQUEST
DELETE /notifications/:notificationid
PATH PARAMETERS
Parameter
Type
Description
notificationid
UUID
ID of notification to be deleted
HTTP RESPONSE
The endpoint returns a 204 No Content  response with an empty body.
POSSIBLE ERRORS
HTTP Status code
Error Code
Description
context
404 Not Found
NOTIFICATION_NOT_FOUND
The given notification was not found
Notification Data Model
Example Notification object
{
  "id": "b7acbf16-7c23-4ef9-89c9-c1223dfe9a17",
  "channel": "WITHDRAWAL_ADDRESS_UPDATE_EMAIL",
  "destination": "test@test.com",
  "label": "Withdrawal address email recipient"
}
Field
Type
Description
id
UUID
The unique identifier of the notification
channel
String
The channel of the wallet
destination
String
Either email or HTTP endpoint
label
String
Human readable label.
