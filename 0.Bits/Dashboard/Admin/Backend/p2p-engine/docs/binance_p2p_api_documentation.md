# Binance P2P API Documentation (Full Conversion)



---

## Page 1

sapi-v7.4.md
2024-05-08
1 / 419
C2C SAPI v7.4
Release Note
Add 6 new APIs:
Get chat image pre signed url
Verify additional kyc
Query CounterParty Order Statistic
Get Payment Method by UserId
Get commission overview
Get taker commission rate
Modify 1 API:
Get Ad Details By Merchant Number (TicketSize replaced by Scale)
Remove the following APIs:
Query Transaction History With Pagination
Query UserInfo Based on Mobile No or Email
Delete Contact
Get Contact List
Get Transfer Detail
Initiate Payment Transfer
Transfer Eligibility Check
). Get All Applicable Ads Category
*. Get Ads Detail By Number
+. Get Ads Reference Price
,. Get Ads List with pagination
.. Post An Ad
/. Search Ads with Condition
1. Update Ads
2. Update Ads Status
3. Query Digital Currency List
)'. Query Fiat Currency List
)). Merchant close business
)*. Merchant End Rest
)+. Get Ad Details By Merchant Number
),. Set Merchant Offline
).. Set Merchant Online
)/. Merchant start business
)1. Merchant Start Rest
)2. Cancel Order
)3. Check If Allowed Cancel Order
*'. Check If Can Place Order
*). Check If Can release Digital Asset
**. Get User Order Detail
*+. Get User Orders Statistic
*,. Retrieve User Order List With Pagination
*.. Retrieve User Order History With Pagination.
*/. Mark Order as Paid
*1. Place An Order
*2. Query Counter Party Order Statistic
*3. Release Digital Asset
+'. Verified additional kyc
+). Get Payment Method by ID
+*. Get Payment Method by UserId
++. List All Of Valid Payment Methods
+,. Get User Detail
+.. Get Risk Warning Tips
+/. Get chat image pre signed url
+1. Mark Messages As Read By User and Order


---

## Page 2

sapi-v7.4.md
2024-05-08
2 / 419
+2. Mark Messages As Read By User
+3. Retrieve Chat WSS URL, Listen Key and Token
,'. Retrieve Chat Messages with Pagination
,). Get commission overview
,*. Get taker commission rate
Here is a step-by-step example of how to send a valid signed payload from the Linux command line using echo, openssl, and curl, using
POST/sapi/v1/c2c/ads/getDetailByNo as example.
Key
Value
apiKey
dbefbc809e3e83c283a984c3a1459732ea7db1360ca80c5c2c8867408d28cc83
secretKey
2b5eb11e18796d12d88f13dc27dbbd02c2cc51ff7059765ed9821957d82bb4d9
Parameter
Value
adsNo
10191633467710386176
timestamp
1591702613943
Example: Use HMAC SHA256 to generate signature for string "adsNo=10191633467710386176&timestamp=1591702613943"
$ echo -n "adsNo=10191633467710386176&timestamp=1591702613943" | openssl dgst -sha256 - hmac
"2b5eb11e18796d12d88f13dc27dbbd02c2cc51ff7059765ed9821957d82bb4d9" (stdin)=
3c661234138461fcc7a7d8746c6558c9842d4e10870d2ecbedf7777cad694af9
Sample curl command of using SAPI (HMAC SHA256), including adsNo, timestamp and signature generated above
$ curl -H "X-MBX-APIKEY:dbefbc809e3e83c283a984c3a1459732ea7db1360ca80c5c2c8867408d28cc83" -X POST
'https://api.binance.com/sapi/v1/c2c/ads/getDetailByNo?
adsNo=10191633467710386176&timestamp=1591702613943&signature=3c661234138461fcc7a7d8746c655 8c9842d4e10870d2ecbedf7777cad694af9'
c2c-ads-controller
Ads Controller
1. Get All Applicable Ads Category
GET /sapi/v1/c2c/ads/getAvailableAdsCategory
Poster
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_UserAdsCategoryResp_
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
2. Get Ads Detail By Number
POST /sapi/v1/c2c/ads/getDetailByNo
Poster
Parameters


---

## Page 3

sapi-v7.4.md
2024-05-08
3 / 419
Name
In
Type
Required
Description
adsNo
query
string
true
adsNo
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_AdDetailResp_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
3. Get Ads Reference Price
POST /sapi/v1/c2c/ads/getReferencePrice
Buyer
Body parameter
{ 
  "assets": [ 
    "string" 
  ], 
  "fiatCurrency": "string", 
  "fromUserRole": "string", 
  "payType": "string", 
  "tradeType": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
AdReferencePriceQueryReq
true
param
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_List_AdReferencePriceResp_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication


---

## Page 4

sapi-v7.4.md
2024-05-08
4 / 419
4. Get Ads List with pagination
POST /sapi/v1/c2c/ads/listWithPagination
Poster
Body parameter
{ 
  "advNo": "string", 
  "advStatus": 0, 
  "asset": "string", 
  "classify": "string", 
  "endDate": "2019-08-24T14:15:22Z", 
  "fiatUnit": "string", 
  "inDeal": 0, 
  "order": "string", 
  "page": 0, 
  "rows": 0, 
  "sort": "string", 
  "startDate": "2019-08-24T14:15:22Z", 
  "tradeType": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
AdQueryByPageReq
true
advQueryByPageReq
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonPageRet_AdDetailResp_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
5. Post An Ad
POST /sapi/v1/c2c/ads/post
Body parameter
{ 
  "asset": "string", 
  "authType": "FIDO2", 
  "autoReplyMsg": "string", 
  "buyerBtcPositionLimit": 0, 
  "buyerKycLimit": 0, 
  "buyerRegDaysLimit": 0, 
  "classify": "string", 
  "code": "string", 
  "emailVerifyCode": "string", 
  "fiatUnit": "string", 
  "googleVerifyCode": "string", 
  "initAmount": 0, 
  "maxSingleTransAmount": 0, 
  "minSingleTransAmount": 0, 
  "mobileVerifyCode": "string", 


---

## Page 5

sapi-v7.4.md
2024-05-08
5 / 419
  "onlineDelayTime": 0, 
  "onlineNow": true, 
  "payTimeLimit": 0, 
  "price": 0, 
  "priceFloatingRatio": 0, 
  "priceType": 0, 
  "rateFloatingRatio": 0, 
  "remarks": "string", 
  "saveAsTemplate": 0, 
  "takerAdditionalKycRequired": 0, 
  "templateName": "string", 
  "tradeMethods": [ 
    { 
      "identifier": "string", 
      "payId": 0, 
      "payType": "string" 
    } 
  ], 
  "tradeType": "string", 
  "userAllTradeCountMax": 0, 
  "userAllTradeCountMin": 0, 
  "userBuyTradeCountMax": 0, 
  "userBuyTradeCountMin": 0, 
  "userSellTradeCountMax": 0, 
  "userSellTradeCountMin": 0, 
  "userTradeCompleteCountMin": 0, 
  "userTradeCompleteRateFilterTime": 0, 
  "userTradeCompleteRateMin": 0, 
  "userTradeCountFilterTime": 0, 
  "userTradeType": 0, 
  "userTradeVolumeAsset": "string", 
  "userTradeVolumeFilterTime": 0, 
  "userTradeVolumeMax": 0, 
  "userTradeVolumeMin": 0, 
  "yubikeyVerifyCode": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
AdPublishReq
true
request
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_string_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
6. Search Ads with Condition
POST /sapi/v1/c2c/ads/search
User
Body parameter
{ 
  "additionalKycVerifyFilter": 0, 


---

## Page 6

sapi-v7.4.md
2024-05-08
6 / 419
  "asset": "string", 
  "countries": [ 
    "string" 
  ], 
  "fiat": "string", 
  "filterType": "string", 
  "order": "string", 
  "page": 0, 
  "payTypes": [ 
    "string" 
  ], 
  "publisherType": "string", 
  "rows": 0, 
  "sort": "string", 
  "tradeType": "string", 
  "transAmount": 0 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
AdSearchReq
true
adSearchReq
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonPageRet_AdSearchResp_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
7. Update Ads
POST /sapi/v1/c2c/ads/update
Poster
Body parameter
{ 
  "advNo": "string", 
  "advStatus": 0, 
  "asset": "string", 
  "authType": "FIDO2", 
  "autoReplyMsg": "string", 
  "buyerBtcPositionLimit": 0, 
  "buyerKycLimit": 0, 
  "buyerRegDaysLimit": 0, 
  "code": "string", 
  "emailVerifyCode": "string", 
  "fiatUnit": "string", 
  "googleVerifyCode": "string", 
  "initAmount": 0, 
  "maxSingleTransAmount": 0, 
  "minSingleTransAmount": 0, 
  "mobileVerifyCode": "string", 
  "payTimeLimit": 0, 
  "price": 0, 
  "priceFloatingRatio": 0, 
  "priceType": 0, 


---

## Page 7

sapi-v7.4.md
2024-05-08
7 / 419
  "rateFloatingRatio": 0, 
  "remarks": "string", 
  "saveAsTemplate": 0, 
  "takerAdditionalKycRequired": 0, 
  "templateName": "string", 
  "tradeMethods": [ 
    { 
      "identifier": "string", 
      "payId": 0, 
      "payType": "string" 
    } 
  ], 
  "tradeType": "string", 
  "updateMode": "string", 
  "userAllTradeCountMax": 0, 
  "userAllTradeCountMin": 0, 
  "userBuyTradeCountMax": 0, 
  "userBuyTradeCountMin": 0, 
  "userSellTradeCountMax": 0, 
  "userSellTradeCountMin": 0, 
  "userTradeCompleteCountMin": 0, 
  "userTradeCompleteRateFilterTime": 0, 
  "userTradeCompleteRateMin": 0, 
  "userTradeCountFilterTime": 0, 
  "userTradeType": 0, 
  "userTradeVolumeAsset": "string", 
  "userTradeVolumeFilterTime": 0, 
  "userTradeVolumeMax": 0, 
  "userTradeVolumeMin": 0, 
  "yubikeyVerifyCode": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
AdUpdateReq
true
adsUpdateReq
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_boolean_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
8. Update Ads Status
POST /sapi/v1/c2c/ads/updateStatus
Poster
Body parameter
{ 
  "advNos": [ 
    "string" 
  ], 
  "advStatus": 0 
} 


---

## Page 8

sapi-v7.4.md
2024-05-08
8 / 419
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
Request_parameters_for_Ads_Status_Batch_Update
true
adsUpdateStatusReq
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_AdUpdateStatusResp_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
c2c-digital-currency-controller
Digital Currency Controller
9. Query Digital Currency List
POST /sapi/v1/c2c/digitalCurrency/list
Poster
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_List_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
c2c-fiat-currency-controller
Fiat Currency Controller
10. Query Fiat Currency List
POST /sapi/v1/c2c/fiatCurrency/list


---

## Page 9

sapi-v7.4.md
2024-05-08
9 / 419
Poster
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_List_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
c2c-merchant-controller
Merchant Controller
11. Merchant close business
POST /sapi/v1/c2c/merchant/closeBusiness
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_boolean_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
12. Merchant End Rest
POST /sapi/v1/c2c/merchant/endRest
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type


---

## Page 10

sapi-v7.4.md
2024-05-08
10 / 419
Name
In
Type
Required
Description
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_boolean_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
13. Get Ad Details By Merchant Number
GET /sapi/v1/c2c/merchant/getAdDetails
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
merchantNo
query
string
false
merchantNo
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_MerchantAdsDetailResp_
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
14. Set Merchant Offline
POST /sapi/v1/c2c/merchant/getOffline
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses


---

## Page 11

sapi-v7.4.md
2024-05-08
11 / 419
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_Void_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
15. Set Merchant Online
POST /sapi/v1/c2c/merchant/getOnline
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_Void_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
16. Merchant start business
POST /sapi/v1/c2c/merchant/startBusiness
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_boolean_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication


---

## Page 12

sapi-v7.4.md
2024-05-08
12 / 419
17. Merchant Start Rest
POST /sapi/v1/c2c/merchant/startRest
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_Merchant_Start_Rest_Response_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
c2c-order-match-controller
Order Match Controller
18. Cancel Order
POST /sapi/v1/c2c/orderMatch/cancelOrder
Body parameter
{ 
  "orderCancelAdditionalInfo": "string", 
  "orderCancelReasonCode": 0, 
  "orderNumber": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
C2C_CancelOrderReq
true
req
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_Void_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None


---

## Page 13

sapi-v7.4.md
2024-05-08
13 / 419
Status
Meaning
Description
Schema
404
Not Found
Not Found
None
This operation does not require authentication
19. Check If Allowed Cancel Order
POST /sapi/v1/c2c/orderMatch/checkIfAllowedCancelOrder
Retrieve
Body parameter
{ 
  "orderNumber": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
OrderNoReq
true
req
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_boolean_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
20. Check If Can Place Order
POST /sapi/v1/c2c/orderMatch/checkIfCanPlaceOrder
Retrieve
Body parameter
{ 
  "adOrderNo": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
AdOrderNoReq
true
adOrderNoReq
Example responses


---

## Page 14

sapi-v7.4.md
2024-05-08
14 / 419
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_boolean_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
21. Check If Can release Digital Asset
POST /sapi/v1/c2c/orderMatch/checkIfCanReleaseCoin
Body parameter
{ 
  "authType": "FIDO2", 
  "code": "string", 
  "confirmPaidType": "string", 
  "emailVerifyCode": "string", 
  "googleVerifyCode": "string", 
  "mobileVerifyCode": "string", 
  "orderNumber": "string", 
  "payId": 0, 
  "yubikeyVerifyCode": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
ConfirmOrderPaidReq
true
confirmOrderPaidReq
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_boolean_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
22. Get User Order Detail
POST /sapi/v1/c2c/orderMatch/getUserOrderDetail
If the query time compared to order created time <= 90days and the order status = completed, payment method name and details will be returned. If the
query time compared to order created time > 90days OR the order status = cancel (including buyer cancel and system cancel), only payment method name
will be returned, payment details will be hidden.
Body parameter


---

## Page 15

sapi-v7.4.md
2024-05-08
15 / 419
{ 
  "adOrderNo": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
AdOrderNoReq
true
adsOrderNoReq
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_OrderMatchResp_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
23. Get User Orders Statistic
GET /sapi/v1/c2c/orderMatch/getUserOrderSummary
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_OrderMatchStatsResp_
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
24. Retrieve User Order List With Pagination
POST /sapi/v1/c2c/orderMatch/listOrders
Body parameter
{ 
  "advNo": "string", 
  "asset": "string", 
  "endDate": 0, 


---

## Page 16

sapi-v7.4.md
2024-05-08
16 / 419
  "order": "string", 
  "orderStatus": 0, 
  "orderStatusList": [ 
    0 
  ], 
  "page": 0, 
  "payType": 0, 
  "rows": 0, 
  "sort": "string", 
  "startDate": 0, 
  "tradeType": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
UserOrderListReq
true
request
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonPageRet_OrderMatchListResp_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
25. Retrieve User Order History With Pagination.
GET /sapi/v1/c2c/orderMatch/listUserOrderHistory
Parameters
Name
In
Type
Required
Description
endTimestamp
query
integer(int64)
false
endTimestamp
page
query
integer(int32)
false
page
rows
query
integer(int32)
false
rows
startTimestamp
query
integer(int64)
false
startTimestamp
tradeType
query
string
false
tradeType
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonPageRet_User_Order_History_
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None


---

## Page 17

sapi-v7.4.md
2024-05-08
17 / 419
Status
Meaning
Description
Schema
404
Not Found
Not Found
None
This operation does not require authentication
26. Mark Order as Paid
POST /sapi/v1/c2c/orderMatch/markOrderAsPaid
Body parameter
{ 
  "orderNumber": "string", 
  "payId": 0 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
MarkOrderAsPaidReq
true
markOrderAsPaidReq
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_MarkOrderAsPaidResp_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
27. Place An Order
POST /sapi/v1/c2c/orderMatch/placeOrder
Body parameter
{ 
  "advOrderNumber": "string", 
  "asset": "string", 
  "buyType": "BY_AMOUNT", 
  "fiatUnit": "string", 
  "matchPrice": 0, 
  "origin": "string", 
  "payId": 0, 
  "payType": "string", 
  "totalAmount": 0, 
  "tradeType": "BUY" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id


---

## Page 18

sapi-v7.4.md
2024-05-08
18 / 419
Name
In
Type
Required
Description
x-user-id
header
string
false
user id
body
body
MakeOrderReq
true
makeOrderReq
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_MakeOrderResp_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
28. Query Counter Party Order Statistic
POST /sapi/v1/c2c/orderMatch/queryCounterPartyOrderStatistic
queryCounterPartyOrderStatistic
Body parameter
{ 
  "orderNumber": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
OrderNoReq
true
orderNoReq
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_UserOrderHistoryStatsResp_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
29. Release Digital Asset
POST /sapi/v1/c2c/orderMatch/releaseCoin
Body parameter
{ 
  "authType": "FIDO2", 
  "code": "string", 
  "confirmPaidType": "string", 


---

## Page 19

sapi-v7.4.md
2024-05-08
19 / 419
  "emailVerifyCode": "string", 
  "googleVerifyCode": "string", 
  "mobileVerifyCode": "string", 
  "orderNumber": "string", 
  "payId": 0, 
  "yubikeyVerifyCode": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
ConfirmOrderPaidReq
true
confirmOrderPaidReq
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_Void_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
30. Verified additional kyc
POST /sapi/v1/c2c/orderMatch/verifiedAdditionalKyc
verifiedAdditionalKyc
Body parameter
{ 
  "orderNumber": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
OrderNoReq
true
arg
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_OrderAdditionalKycVerifyResp_
201
Created
Created
None
401
Unauthorized
Unauthorized
None


---

## Page 20

sapi-v7.4.md
2024-05-08
20 / 419
Status
Meaning
Description
Schema
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
c2c-payment-method-controller
Payment Method Controller
31. Get Payment Method by ID
GET /sapi/v1/c2c/paymentMethod/getPayMethodById
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
id
query
integer(int64)
true
id
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_PayMethodResp_
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
32. Get Payment Method by UserId
GET /sapi/v1/c2c/paymentMethod/getPayMethodByUserId
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_List_PayMethodResp_
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
33. List All Of Valid Payment Methods


---

## Page 21

sapi-v7.4.md
2024-05-08
21 / 419
POST /sapi/v1/c2c/paymentMethod/listAll
Payment Method List
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonPageRet_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
c2c-user-controller
C 2 C User Controller
34. Get User Detail
POST /sapi/v1/c2c/user/baseDetail
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_FiatUserDetailResp_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
c2c_chat_controller
C 2 C Chat Controller
35. Get Risk Warning Tips


---

## Page 22

sapi-v7.4.md
2024-05-08
22 / 419
POST /sapi/v1/c2c/chat/getRiskWarningTips
Body parameter
{ 
  "fiat": "string", 
  "orderNo": "string", 
  "scene": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
RiskWarningTipsReq
true
riskWarningTipsReq
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_RiskWarningTipsResp_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
36. Get chat image pre signed url
POST /sapi/v1/c2c/chat/image/pre-signed-url
Body parameter
{ 
  "imageName": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
FetchImageUploadUrlArg
true
arg
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_FetchImageUploadUrlRet_
201
Created
Created
None


---

## Page 23

sapi-v7.4.md
2024-05-08
23 / 419
Status
Meaning
Description
Schema
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
37. Mark Messages As Read By User and Order
POST /sapi/v1/c2c/chat/markOrderMessagesAsRead
Body parameter
{ 
  "orderNo": "string", 
  "userId": 0 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
MarkOrderMessageAsReadReq
true
markOrderMessageAsReadReq
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_Void_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
38. Mark Messages As Read By User
POST /sapi/v1/c2c/chat/markUserMessagesAsRead
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_Void_
201
Created
Created
None


---

## Page 24

sapi-v7.4.md
2024-05-08
24 / 419
Status
Meaning
Description
Schema
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
39. Retrieve Chat WSS URL, Listen Key and Token
GET /sapi/v1/c2c/chat/retrieveChatCredential
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_ChatCredentialResp_
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
40. Retrieve Chat Messages with Pagination
GET /sapi/v1/c2c/chat/retrieveChatMessagesWithPagination
Parameters
Name
In
Type
Required
Description
chatMessageType
query
string
false
chat message type: text/image etc
clientType
header
string
true
Client Device Type
id
query
integer(int64)
false
Query message ID, optional. It will be used as one of the query conditions, the queried message ID
< the provided ID
order
query
string
false
Page order by
orderNo
query
string
false
Order number
page
query
integer(int32)
true
Page number to query. Start = 1
rows
query
integer(int32)
true
Rows to query per page. Suggested = 20
sort
query
string
false
Page sorting by (asc, desc)
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonPageRet_RetrieveChatMessagesWithPaginationResp_
401
Unauthorized
Unauthorized
None


---

## Page 25

sapi-v7.4.md
2024-05-08
25 / 419
Status
Meaning
Description
Schema
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
c2c_commission_rate_controller
Commission Rate Controller
41. Get commission overview
POST /sapi/v1/c2c/commission-rate/overview
Body parameter
{ 
  "fiat": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
commission_rate
true
arg
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_commission_rate_overview_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
42. Get taker commission rate
POST /sapi/v1/c2c/commission-rate/taker
Body parameter
{ 
  "area": "string", 
  "asset": "string", 
  "classify": "string", 
  "fiat": "string", 
  "tradeMethodIdentifier": [ 
    "string" 
  ], 
  "tradeType": "string" 
} 
Parameters
Name
In
Type
Required
Description
clientType
header
string
true
Client Device Type


---

## Page 26

sapi-v7.4.md
2024-05-08
26 / 419
Name
In
Type
Required
Description
x-gray-env
header
string
false
env flag
x-trace-id
header
string
false
x-trace-id
x-user-id
header
string
false
user id
body
body
taker_commission_rate0
true
arg
Example responses
200 Response
Responses
Status
Meaning
Description
Schema
200
OK
OK
CommonRet_List_taker_commission_rate_
201
Created
Created
None
401
Unauthorized
Unauthorized
None
403
Forbidden
Forbidden
None
404
Not Found
Not Found
None
This operation does not require authentication
Schemas
AccountDetail
{ 
  "baseAsset": { 
    "userId": 0, 
    "value": 0 
  }, 
  "enabled": true, 
  "indexPrice": 0, 
  "isolatedCreated": true, 
  "liquidatePrice": 0, 
  "liquidateRate": 0, 
  "marginLevel": 0, 
  "marginLevelStatus": "string", 
  "marginRatio": 0, 
  "quoteAsset": { 
    "userId": 0, 
    "value": 0 
  }, 
  "symbol": "string", 
  "tradeEnabled": true 
} 
 
AccountDetail
42.1. Properties
Name
Type
Required
Restrictions
Description
baseAsset
UserAsset
false
none
none
enabled
boolean
false
none
none
indexPrice
number
false
none
none
isolatedCreated
boolean
false
none
none
liquidatePrice
number
false
none
none
liquidateRate
number
false
none
none
marginLevel
number
false
none
none
marginLevelStatus
string
false
none
none
marginRatio
number
false
none
none
quoteAsset
UserAsset
false
none
none


---

## Page 27

sapi-v7.4.md
2024-05-08
27 / 419
Name
Type
Required
Restrictions
Description
symbol
string
false
none
none
tradeEnabled
boolean
false
none
none
AccountDetailResp
{ 
  "accountType": "string", 
  "borrowEnabled": true, 
  "collateralMarginLevel": 0, 
  "marginLevel": 0, 
  "totalAssetOfBtc": 0, 
  "totalCollateralValueInUSDT": 0, 
  "totalLiabilityOfBtc": 0, 
  "totalNetAssetOfBtc": 0, 
  "tradeEnabled": true, 
  "transferEnabled": true, 
  "userAssets": [ 
    { 
      "userId": 0, 
      "value": 0 
    } 
  ] 
} 
 
AccountDetailResp
42.2. Properties
Name
Type
Required
Restrictions
Description
accountType
string
false
none
none
borrowEnabled
boolean
false
none
none
collateralMarginLevel
number
false
none
none
marginLevel
number
false
none
none
totalAssetOfBtc
number
false
none
none
totalCollateralValueInUSDT
number
false
none
none
totalLiabilityOfBtc
number
false
none
none
totalNetAssetOfBtc
number
false
none
none
tradeEnabled
boolean
false
none
none
transferEnabled
boolean
false
none
none
userAssets
[UserAsset]
false
none
none
AccountIndicateResponse
{ 
  "accountEquity": 0, 
  "accountInitialMargin": 0, 
  "accountMaintMargin": 0, 
  "accountStatus": "string", 
  "accountType": "string", 
  "actualEquity": 0, 
  "totalAvailableBalance": 0, 
  "uniMMR": 0 
} 
 
AccountIndicateResponse
42.3. Properties
Name
Type
Required
Restrictions
Description
accountEquity
number
false
none
none


---

## Page 28

sapi-v7.4.md
2024-05-08
28 / 419
Name
Type
Required
Restrictions
Description
accountInitialMargin
number
false
none
none
accountMaintMargin
number
false
none
none
accountStatus
string
false
none
none
accountType
string
false
none
none
actualEquity
number
false
none
none
totalAvailableBalance
number
false
none
none
uniMMR
number
false
none
none
AccountResp
{ 
  "totalAmountInBTC": 0, 
  "totalAmountInUSDT": 0, 
  "totalFlexibleAmountInBTC": 0, 
  "totalFlexibleAmountInUSDT": 0, 
  "totalLockedInBTC": 0, 
  "totalLockedInUSDT": 0 
} 
 
AccountResp
42.4. Properties
Name
Type
Required
Restrictions
Description
totalAmountInBTC
number
false
none
none
totalAmountInUSDT
number
false
none
none
totalFlexibleAmountInBTC
number
false
none
none
totalFlexibleAmountInUSDT
number
false
none
none
totalLockedInBTC
number
false
none
none
totalLockedInUSDT
number
false
none
none
AccountResponse
{ 
  "cumulativeProfitInBETH": 0, 
  "lastDayProfitInBETH": 0 
} 
 
AccountResponse
42.5. Properties
Name
Type
Required
Restrictions
Description
cumulativeProfitInBETH
number
false
none
none
lastDayProfitInBETH
number
false
none
none
AccountSnapshotResp
{ 
  "code": 0, 
  "msg": "string", 
  "snapshotVos": [ 
    { 
      "data": {}, 
      "type": "string", 
      "updateTime": 0 
    } 
  ] 


---

## Page 29

sapi-v7.4.md
2024-05-08
29 / 419
} 
 
AccountSnapshotResp
42.6. Properties
Name
Type
Required
Restrictions
Description
code
integer(int32)
false
none
none
msg
string
false
none
none
snapshotVos
[AccountSnapshotVo_object_]
false
none
none
AccountTypeInfoVo
{ 
  "parentUserId": "string", 
  "remark": "string", 
  "subUser": true, 
  "userId": "string", 
  "userStatusEx": {} 
} 
 
AccountTypeInfoVo
42.7. Properties
Name
Type
Required
Restrictions
Description
parentUserId
string
false
none
该字段为账户类型 0--其他账户类型; 1--账户类型为⺟账户; 如果是⼦账户, 该字段设置成⺟账户uid
remark
string
false
none
remark
subUser
boolean
false
none
none
userId
string
false
none
user id
userStatusEx
object
false
none
状态位
AccountV2Response
{ 
  "holdingInETH": 0, 
  "holdings": { 
    "bethAmount": 0, 
    "wbethAmount": 0 
  }, 
  "profit": { 
    "amountFromBETH": 0, 
    "amountFromWBETH": 0 
  }, 
  "thirtyDaysProfitInETH": 0 
} 
 
AccountV2Response
42.8. Properties
Name
Type
Required
Restrictions
Description
holdingInETH
number
false
none
none
holdings
EthHoldingDetail
false
none
none
profit
EthProfitDetail
false
none
none
thirtyDaysProfitInETH
number
false
none
none
AdDetailResp


---

## Page 30

sapi-v7.4.md
2024-05-08
30 / 419
{ 
  "advNo": "string", 
  "advStatus": 0, 
  "advUpdateTime": "2019-08-24T14:15:22Z", 
  "advVisibleRet": { 
    "freeAmountVisible": 0, 
    "orderFlowVisible": 0, 
    "surplusAmountVisible": 0, 
    "userSetVisible": 0 
  }, 
  "asset": "string", 
  "assetLogo": "string", 
  "assetScale": 0, 
  "assetVo": { 
    "asset": "string", 
    "decimalScale": 0, 
    "iconUrl": "string", 
    "name": "string" 
  }, 
  "autoReplyMsg": "string", 
  "buyerBtcPositionLimit": 0, 
  "buyerKycLimit": 0, 
  "buyerRegDaysLimit": 0, 
  "classify": "string", 
  "commissionRate": 0, 
  "createTime": "2019-08-24T14:15:22Z", 
  "currencyRate": 0, 
  "dynamicMaxSingleTransAmount": 0, 
  "dynamicMaxSingleTransQuantity": 0, 
  "fiatScale": 0, 
  "fiatSymbol": "string", 
  "fiatUnit": "string", 
  "fiatVo": { 
    "countryCode": "string", 
    "currencyCode": "string", 
    "currencyScale": 0, 
    "currencySymbol": "string", 
    "iconUrl": "string", 
    "priceScale": 0 
  }, 
  "initAmount": 0, 
  "isTradable": true, 
  "maxSingleTransAmount": 0, 
  "maxSingleTransQuantity": 0, 
  "minSingleTransAmount": 0, 
  "minSingleTransQuantity": 0, 
  "offlineReason": "string", 
  "payTimeLimit": 0, 
  "price": 0, 
  "priceFloatingRatio": 0, 
  "priceScale": 0, 
  "priceType": 0, 
  "rateFloatingRatio": 0, 
  "remarks": "string", 
  "surplusAmount": 0, 
  "takerAdditionalKycRequired": 0, 
  "tradableQuantity": 0, 
  "tradeMethodCommissionRateVoList": [ 
    { 
      "commissionRate": 0, 
      "tradeMethodIdentifier": "string", 
      "tradeMethodName": "string" 
    } 
  ], 
  "tradeMethods": [ 
    { 
      "iconUrlColor": "string", 
      "identifier": "string", 
      "payAccount": "string", 
      "payBank": "string", 
      "payId": 0, 
      "paySubBank": "string", 
      "payType": "string", 
      "tradeMethodName": "string" 
    } 
  ], 
  "tradeType": "string", 
  "userAllTradeCountMax": 0, 
  "userAllTradeCountMin": 0, 
  "userBuyTradeCountMax": 0, 


---

## Page 31

sapi-v7.4.md
2024-05-08
31 / 419
  "userBuyTradeCountMin": 0, 
  "userSellTradeCountMax": 0, 
  "userSellTradeCountMin": 0, 
  "userTradeCompleteCountMin": 0, 
  "userTradeCompleteRateFilterTime": 0, 
  "userTradeCompleteRateMin": 0, 
  "userTradeCountFilterTime": 0, 
  "userTradeType": 0, 
  "userTradeVolumeAsset": "string", 
  "userTradeVolumeFilterTime": 0, 
  "userTradeVolumeMax": 0, 
  "userTradeVolumeMin": 0 
} 
 
AdDetailResp
42.9. Properties
Name
Type
Required
Restrictions
Description
advNo
string
false
none
Adv number
advStatus
integer(int32)
false
none
Adv status， 1: Online，3: Offline，4ÏClosed
advUpdateTime
string(date-time)
false
none
Adv update time
advVisibleRet
AdVisibleRetVo
false
none
Advertisement hidden information
asset
string
false
none
Adv asset: BTC
assetLogo
string
false
none
none
assetScale
integer(int32)
false
none
Asset decimal precision
assetVo
Asset_detail
false
none
Asset detail
autoReplyMsg
string
false
none
Auto reply message
buyerBtcPositionLimit
number
false
none
Require buyer minimum BTC asset position
buyerKycLimit
integer(int32)
false
none
Require buyer kyc verified. 0: No, 1: Yes
buyerRegDaysLimit
integer(int32)
false
none
Require buyer minimum registered day. 0: No, 1: Yes
classify
string
false
none
Adv classify. mass
commissionRate
number
false
none
Commission rate for the adv
createTime
string(date-time)
false
none
Adv create time
currencyRate
number
false
none
Currency exchange rate
dynamicMaxSingleTransAmount
number
false
none
Dynamic maximum single transaction amount
dynamicMaxSingleTransQuantity
number
false
none
Dynamic maximum single transaction quantity
fiatScale
integer(int32)
false
none
Fiat decimal precision
fiatSymbol
string
false
none
Fiat symbol
fiatUnit
string
false
none
Fiat currency: CNY
fiatVo
Fiat_detail
false
none
Fiat detail
initAmount
number
false
none
Adv amount
isTradable
boolean
false
none
If user is able to trade with the advertisement
maxSingleTransAmount
number
false
none
Single transaction maximum amount in fiat
maxSingleTransQuantity
number
false
none
Maximum single transaction quantity
minSingleTransAmount
number
false
none
Single transaction minimum amount in fiat
minSingleTransQuantity
number
false
none
Minimum single transaction quantity
offlineReason
string
false
none
offline reason code
payTimeLimit
integer(int32)
false
none
Maximum time waiting for payment in minute
price
number
false
none
Adv price
priceFloatingRatio
number
false
none
Floating price ratio of the adv
priceScale
integer(int32)
false
none
Asset price decimal precision


---

## Page 32

sapi-v7.4.md
2024-05-08
32 / 419
Name
Type
Required
Restrictions
Description
priceType
integer(int32)
false
none
Adv price type. 1: FIXED, 2: FLOATING
rateFloatingRatio
number
false
none
Exchange rate ration of the trading pair
remarks
string
false
none
Remark
surplusAmount
number
false
none
Adv remaining amount
takerAdditionalKycRequired
integer(int32)
false
none
whether taker additional kyc required: 0 not required 1
required
tradableQuantity
number
false
none
Tradeable quantity of the adv
tradeMethodCommissionRateVoList
[TradeMethodCommissionRateVo]
false
none
Commission rate by payment method
tradeMethods
[AdTradeMethodResp]
false
none
List of accepted payment method for the adv
tradeType
string
false
none
Adv trade type. 0: BUY, 1: SELL
userAllTradeCountMax
integer(int32)
false
none
Require user maximum all trades
userAllTradeCountMin
integer(int32)
false
none
Require user minimum all trades
userBuyTradeCountMax
integer(int32)
false
none
Require user maximum buy trades
userBuyTradeCountMin
integer(int32)
false
none
Require user minimum buy trades
userSellTradeCountMax
integer(int32)
false
none
Require user maximum sell trades
userSellTradeCountMin
integer(int32)
false
none
Require user minimum sell trades
userTradeCompleteCountMin
integer(int32)
false
none
Require user minimum completed trades
userTradeCompleteRateFilterTime
integer(int32)
false
none
Filter user completion rate type. 1: Last 30D, 2: All-time
userTradeCompleteRateMin
number
false
none
Require user minimum completion rate
userTradeCountFilterTime
integer(int32)
false
none
Filter user trade count type. 1: Last 30D, 2: All-time
userTradeType
integer(int32)
false
none
User trade volume tradeType. 0: BUY, 1: SELL, 2: ALL
userTradeVolumeAsset
string
false
none
User trade volume asset for requirement
userTradeVolumeFilterTime
integer(int32)
false
none
Filter user trade volume. 1: Last 30D, 2: All-time
userTradeVolumeMax
number
false
none
Require user maximum trade volume
userTradeVolumeMin
number
false
none
Require user minimum trade volume
AdDetailVo
{ 
  "adVisibleRet": { 
    "freeAmountVisible": 0, 
    "orderFlowVisible": 0, 
    "surplusAmountVisible": 0, 
    "userSetVisible": 0 
  }, 
  "advNo": "string", 
  "asset": "string", 
  "assetScale": 0, 
  "assetTicketSize": "string", 
  "autoReply": "string", 
  "buyerBtcAmount": 0, 
  "buyerRegisterLimit": 0, 
  "currencyTicketSize": "string", 
  "dynamicMaxOrderAmount": 0, 
  "dynamicMaxOrderPrice": 0, 
  "fiatScale": 0, 
  "fiatSymbol": "string", 
  "fiatUnit": "string", 
  "isConformed": true, 
  "kycLimit": 0, 
  "logo": "string", 
  "mainUserId": 0, 
  "maxOrderAmount": 0, 
  "maxOrderPrice": 0, 
  "minOrderAmount": 0, 
  "minOrderPrice": 0, 
  "offlineReason": "string", 
  "payMethodDtos": [ 
    { 
      "iconUrlColor": "string", 


---

## Page 33

sapi-v7.4.md
2024-05-08
33 / 419
      "id": 0, 
      "identifier": "string", 
      "payAccount": "string", 
      "payBank": "string", 
      "payMethodId": "string", 
      "paySubBank": "string", 
      "payType": "string", 
      "tradeMethodBgColor": "string", 
      "tradeMethodName": "string", 
      "tradeMethodShortName": "string" 
    } 
  ], 
  "payTimeLimit": 0, 
  "payTypeList": [ 
    "string" 
  ], 
  "price": 0, 
  "priceScale": 0, 
  "priceTicketSize": "string", 
  "remark": "string", 
  "surplusAmount": 0, 
  "takerAdditionalKycRequired": 0, 
  "tradeType": "BUY", 
  "userId": 0 
} 
 
AdDetailVo
42.10. Properties
Name
Type
Required
Restrictions
Description
adVisibleRet
AdVisibleRetVo
false
none
Advertisement hidden information
advNo
string
false
none
Adv number
asset
string
false
none
Crypto asset: BTC
assetScale
integer(int32)
false
none
Asset currency decimal precision
assetTicketSize
string
false
none
Asset currency decimal precision
autoReply
string
false
none
Automatic reply message for orders
buyerBtcAmount
number
false
none
Equivalent BTC holding of buyer
buyerRegisterLimit
integer(int32)
false
none
Limit for buyer registration days, default 60, maximum 180 days
currencyTicketSize
string
false
none
Fiat currency decimal precision
dynamicMaxOrderAmount
number
false
none
Dynamic maximum transaction quantity
dynamicMaxOrderPrice
number
false
none
Dynamic maximum transaction amount
fiatScale
integer(int32)
false
none
Fiat currency decimal precision
fiatSymbol
string
false
none
Fiat symbol
fiatUnit
string
false
none
Fiat currency: CNY
isConformed
boolean
false
none
Whether the current logged in user meets the requirements of the advertisement
kycLimit
integer(int32)
false
none
KYC user registration limit, complete or not. (0: Not required, 1: Yes)
logo
string
false
none
Logo
mainUserId
integer(int64)
false
none
Advertisement merchant id
maxOrderAmount
number
false
none
Maximum transaction quantity
maxOrderPrice
number
false
none
Maximum transaction amount
minOrderAmount
number
false
none
Minimum transaction quantity
minOrderPrice
number
false
none
Minimum transaction amount
offlineReason
string
false
none
offline reason code
payMethodDtos
[PayMethodDto]
false
none
List of accepted trading method
payTimeLimit
integer(int32)
false
none
Payment time limit, in minutes
payTypeList
[string]
false
none
Payment method list, e.g.: BANK, WECHAT. Deprecated, use payMethodDtos
price
number
false
none
Price


---

## Page 34

sapi-v7.4.md
2024-05-08
34 / 419
Name
Type
Required
Restrictions
Description
priceScale
integer(int32)
false
none
Price decimal precision
priceTicketSize
string
false
none
Price decimal precision
remark
string
false
none
Remark
surplusAmount
number
false
none
Adv remaining amount
takerAdditionalKycRequired
integer(int32)
false
none
whether taker additional kyc required: 0 not required 1 required
tradeType
string
false
none
Adv trade type. 0: BUY, 1ÏSELL
userId
integer(int64)
false
none
none
42.10.1. Enumerated Values
Property
Value
tradeType
BUY
tradeType
SELL
AdOrderNoReq
{ 
  "adOrderNo": "string" 
} 
 
AdOrderNoReq
42.11. Properties
Name
Type
Required
Restrictions
Description
adOrderNo
string
false
none
Order number
AdPublishReq
{ 
  "asset": "string", 
  "authType": "FIDO2", 
  "autoReplyMsg": "string", 
  "buyerBtcPositionLimit": 0, 
  "buyerKycLimit": 0, 
  "buyerRegDaysLimit": 0, 
  "classify": "string", 
  "code": "string", 
  "emailVerifyCode": "string", 
  "fiatUnit": "string", 
  "googleVerifyCode": "string", 
  "initAmount": 0, 
  "maxSingleTransAmount": 0, 
  "minSingleTransAmount": 0, 
  "mobileVerifyCode": "string", 
  "onlineDelayTime": 0, 
  "onlineNow": true, 
  "payTimeLimit": 0, 
  "price": 0, 
  "priceFloatingRatio": 0, 
  "priceType": 0, 
  "rateFloatingRatio": 0, 
  "remarks": "string", 
  "saveAsTemplate": 0, 
  "takerAdditionalKycRequired": 0, 
  "templateName": "string", 
  "tradeMethods": [ 
    { 
      "identifier": "string", 
      "payId": 0, 
      "payType": "string" 
    } 
  ], 
  "tradeType": "string", 
  "userAllTradeCountMax": 0, 
  "userAllTradeCountMin": 0, 


---

## Page 35

sapi-v7.4.md
2024-05-08
35 / 419
  "userBuyTradeCountMax": 0, 
  "userBuyTradeCountMin": 0, 
  "userSellTradeCountMax": 0, 
  "userSellTradeCountMin": 0, 
  "userTradeCompleteCountMin": 0, 
  "userTradeCompleteRateFilterTime": 0, 
  "userTradeCompleteRateMin": 0, 
  "userTradeCountFilterTime": 0, 
  "userTradeType": 0, 
  "userTradeVolumeAsset": "string", 
  "userTradeVolumeFilterTime": 0, 
  "userTradeVolumeMax": 0, 
  "userTradeVolumeMin": 0, 
  "yubikeyVerifyCode": "string" 
} 
 
AdPublishReq
42.12. Properties
Name
Type
Required
Restrictions
Description
asset
string
true
none
Crypto asset: BTC
authType
string
false
none
Authenticate code type: GOOGLE
autoReplyMsg
string
false
none
Auto reply message
buyerBtcPositionLimit
number
false
none
Require buyer minimum BTC asset position
buyerKycLimit
integer(int32)
true
none
Require buyer kyc verified. 0: No, 1: Yes
buyerRegDaysLimit
integer(int32)
false
none
Require buyer minimum registered day. 0: No, 1: Yes
classify
string
true
none
Adv classify. mass
code
string
false
none
Authenticate Code
emailVerifyCode
string
false
none
Email verification code
fiatUnit
string
true
none
Fiat currency: CNY
googleVerifyCode
string
false
none
Google verification code
initAmount
number
true
none
Adv amount
maxSingleTransAmount
number
true
none
Single transaction maximum amount in fiat
minSingleTransAmount
number
true
none
Single transaction minimum amount in fiat
mobileVerifyCode
string
false
none
Mobile verification code
onlineDelayTime
integer(int32)
false
none
Adv to be online after some delay
onlineNow
boolean
false
none
Adv to be online immediately
payTimeLimit
integer(int32)
false
none
Maximum time waiting for payment in minute
price
number
false
none
Adv price
priceFloatingRatio
number
false
none
Floating price ratio of the adv
priceType
integer(int32)
true
none
Adv price type. 1: FIXED, 2: FLOATING
rateFloatingRatio
number
false
none
Exchange rate ration of the trading pair
remarks
string
false
none
Remark
saveAsTemplate
integer(int32)
false
none
Adv as template. 0: No, 1: Yes
takerAdditionalKycRequired
integer(int32)
false
none
whether taker additional kyc required: 0 not required 1 required
templateName
string
false
none
Template name
tradeMethods
[AdsTradeMethodVo]
true
none
List of accepted payment method for the adv
tradeType
string
true
none
Adv trade type. 0: BUY, 1: SELL
userAllTradeCountMax
integer(int32)
false
none
Require user maximum all trades
userAllTradeCountMin
integer(int32)
false
none
Require user minimum all trades
userBuyTradeCountMax
integer(int32)
false
none
Require user maximum buy trades
userBuyTradeCountMin
integer(int32)
false
none
Require user minimum buy trades


---

## Page 36

sapi-v7.4.md
2024-05-08
36 / 419
Name
Type
Required
Restrictions
Description
userSellTradeCountMax
integer(int32)
false
none
Require user maximum sell trades
userSellTradeCountMin
integer(int32)
false
none
Require user minimum sell trades
userTradeCompleteCountMin
integer(int32)
false
none
Require user minimum completed trades
userTradeCompleteRateFilterTime
integer(int32)
false
none
Filter user completion rate type. 1: Last 30D, 2: All-time
userTradeCompleteRateMin
number
false
none
Require user minimum completion rate
userTradeCountFilterTime
integer(int32)
false
none
Filter user trade count type. 1: Last 30D, 2: All-time
userTradeType
integer(int32)
false
none
User trade volume tradeType. 0: BUY, 1: SELL, 2: ALL
userTradeVolumeAsset
string
false
none
User trade volume asset for requirement
userTradeVolumeFilterTime
integer(int32)
false
none
Filter user trade volume. 1: Last 30D, 2: All-time
userTradeVolumeMax
number
false
none
Require user maximum trade volume
userTradeVolumeMin
number
false
none
Require user minimum trade volume
yubikeyVerifyCode
string
false
none
Yubikey verification code
42.12.1. Enumerated Values
Property
Value
authType
FIDO2
authType
FUND_PWD
authType
GOOGLE
authType
SMS
AdQueryByPageReq
{ 
  "advNo": "string", 
  "advStatus": 0, 
  "asset": "string", 
  "classify": "string", 
  "endDate": "2019-08-24T14:15:22Z", 
  "fiatUnit": "string", 
  "inDeal": 0, 
  "order": "string", 
  "page": 0, 
  "rows": 0, 
  "sort": "string", 
  "startDate": "2019-08-24T14:15:22Z", 
  "tradeType": "string" 
} 
 
AdQueryByPageReq
42.13. Properties
Name
Type
Required
Restrictions
Description
advNo
string
false
none
Adv number
advStatus
integer(int32)
false
none
Adv status， 1: Online，3: Offline，4ÏClosed
asset
string
false
none
Crypto asset: BTC
classify
string
false
none
Adv classify. mass
endDate
string(date-time)
false
none
Query date range endDate
fiatUnit
string
false
none
Fiat currency, e.g.: CNY, USD, if not provided, returns all fiat currency types
inDeal
integer(int32)
false
none
Query advertisements which are available to trade
order
string
false
none
Page order by
page
integer(int32)
true
none
Page number to query. Start = 1
rows
integer(int32)
true
none
Rows to query per page. Suggested = 20


---

## Page 37

sapi-v7.4.md
2024-05-08
37 / 419
Name
Type
Required
Restrictions
Description
sort
string
false
none
Page sorting by (asc, desc)
startDate
string(date-time)
false
none
Query date range startDate
tradeType
string
false
none
Adv trade type. 0: BUY, 1: SELL
AdReferencePriceQueryReq
{ 
  "assets": [ 
    "string" 
  ], 
  "fiatCurrency": "string", 
  "fromUserRole": "string", 
  "payType": "string", 
  "tradeType": "string" 
} 
 
AdReferencePriceQueryReq
42.14. Properties
Name
Type
Required
Restrictions
Description
assets
[string]
false
none
List of asset (maximum 3) eg: BTC
fiatCurrency
string
true
none
Fiat currency, e.g.: CNY
fromUserRole
string
false
none
Role of the user that Adv quote come from. USER, ADVERTISER, default: ADVERTISER if not present
payType
string
false
none
Payment method, e.g.: BANK, WECHAT
tradeType
string
true
none
Adv trade type. 0: BUY, 1: SELL
AdReferencePriceResp
{ 
  "asset": "string", 
  "assetScale": 0, 
  "currency": "string", 
  "currencyScale": 0, 
  "currencySymbol": "string", 
  "priceScale": 0, 
  "referencePrice": 0 
} 
 
AdReferencePriceResp
42.15. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
Crypto asset: BTC
assetScale
integer(int32)
false
none
Asset decimal precision
currency
string
false
none
Advertisement fiat currency
currencyScale
integer(int32)
false
none
Fiat currency decimal precision
currencySymbol
string
false
none
Fiat currency symbol
priceScale
integer(int32)
false
none
Asset price decimal precision
referencePrice
number
false
none
Advertisement reference quote
AdSearchReq
{ 
  "additionalKycVerifyFilter": 0, 
  "asset": "string", 
  "countries": [ 
    "string" 


---

## Page 38

sapi-v7.4.md
2024-05-08
38 / 419
  ], 
  "fiat": "string", 
  "filterType": "string", 
  "order": "string", 
  "page": 0, 
  "payTypes": [ 
    "string" 
  ], 
  "publisherType": "string", 
  "rows": 0, 
  "sort": "string", 
  "tradeType": "string", 
  "transAmount": 0 
} 
 
AdSearchReq
42.16. Properties
Name
Type
Required
Restrictions
Description
additionalKycVerifyFilter
integer(int32)
false
none
additionalKycVerifyFilter: 0 don't use this filter, return both 1 return no need
additionalKycVerify ad only
asset
string
true
none
Crypto asset: BTC
countries
[string]
false
none
Adv launch countries, return all countries result if not present
fiat
string
true
none
Fiat currency: CNY
filterType
string
false
none
Filter type (tradable displays ads that users can trade, all displays all ads, considering
expanding other filter types), effective after user login, default is 'all'
order
string
false
none
Page order by
page
integer(int32)
true
none
Page number to query. Start = 1
payTypes
[string]
false
none
Payment method list, e.g.: BANK, WECHAT
publisherType
string
false
none
Adv publisher type (user, merchant). Return all if not present
rows
integer(int32)
true
none
Rows to query per page. Suggested = 20
sort
string
false
none
Page sorting by (asc, desc)
tradeType
string
true
none
User trade type: BUY, SELL; e.g.: for user purchasing, provide value 'BUY'
transAmount
number
false
none
Transaction amount
AdSearchResp
{ 
  "adv": { 
    "advNo": "string", 
    "advStatus": 0, 
    "advUpdateTime": "2019-08-24T14:15:22Z", 
    "advVisibleRet": { 
      "freeAmountVisible": 0, 
      "orderFlowVisible": 0, 
      "surplusAmountVisible": 0, 
      "userSetVisible": 0 
    }, 
    "asset": "string", 
    "assetLogo": "string", 
    "assetScale": 0, 
    "assetVo": { 
      "asset": "string", 
      "decimalScale": 0, 
      "iconUrl": "string", 
      "name": "string" 
    }, 
    "autoReplyMsg": "string", 
    "buyerBtcPositionLimit": 0, 
    "buyerKycLimit": 0, 
    "buyerRegDaysLimit": 0, 
    "classify": "string", 
    "commissionRate": 0, 
    "createTime": "2019-08-24T14:15:22Z", 
    "currencyRate": 0, 
    "dynamicMaxSingleTransAmount": 0, 


---

## Page 39

sapi-v7.4.md
2024-05-08
39 / 419
    "dynamicMaxSingleTransQuantity": 0, 
    "fiatScale": 0, 
    "fiatSymbol": "string", 
    "fiatUnit": "string", 
    "fiatVo": { 
      "countryCode": "string", 
      "currencyCode": "string", 
      "currencyScale": 0, 
      "currencySymbol": "string", 
      "iconUrl": "string", 
      "priceScale": 0 
    }, 
    "initAmount": 0, 
    "isTradable": true, 
    "maxSingleTransAmount": 0, 
    "maxSingleTransQuantity": 0, 
    "minSingleTransAmount": 0, 
    "minSingleTransQuantity": 0, 
    "offlineReason": "string", 
    "payTimeLimit": 0, 
    "price": 0, 
    "priceFloatingRatio": 0, 
    "priceScale": 0, 
    "priceType": 0, 
    "rateFloatingRatio": 0, 
    "remarks": "string", 
    "surplusAmount": 0, 
    "takerAdditionalKycRequired": 0, 
    "tradableQuantity": 0, 
    "tradeMethodCommissionRateVoList": [ 
      { 
        "commissionRate": 0, 
        "tradeMethodIdentifier": "string", 
        "tradeMethodName": "string" 
      } 
    ], 
    "tradeMethods": [ 
      { 
        "iconUrlColor": "string", 
        "identifier": "string", 
        "payAccount": "string", 
        "payBank": "string", 
        "payId": 0, 
        "paySubBank": "string", 
        "payType": "string", 
        "tradeMethodName": "string" 
      } 
    ], 
    "tradeType": "string", 
    "userAllTradeCountMax": 0, 
    "userAllTradeCountMin": 0, 
    "userBuyTradeCountMax": 0, 
    "userBuyTradeCountMin": 0, 
    "userSellTradeCountMax": 0, 
    "userSellTradeCountMin": 0, 
    "userTradeCompleteCountMin": 0, 
    "userTradeCompleteRateFilterTime": 0, 
    "userTradeCompleteRateMin": 0, 
    "userTradeCountFilterTime": 0, 
    "userTradeType": 0, 
    "userTradeVolumeAsset": "string", 
    "userTradeVolumeFilterTime": 0, 
    "userTradeVolumeMax": 0, 
    "userTradeVolumeMin": 0 
  }, 
  "advertiser": { 
    "advConfirmTime": 0, 
    "email": "string", 
    "margin": 0, 
    "marginUnit": "string", 
    "mobile": "string", 
    "monthFinishRate": 0, 
    "monthOrderCount": 0, 
    "nickName": "string", 
    "orderCount": 0, 
    "realName": "string", 
    "registrationTime": "2019-08-24T14:15:22Z", 
    "tagIconUrls": [ 
      "string" 
    ], 
    "userNo": "string", 


---

## Page 40

sapi-v7.4.md
2024-05-08
40 / 419
    "userType": "string" 
  } 
} 
 
AdSearchResp
42.17. Properties
Name
Type
Required
Restrictions
Description
adv
AdDetailResp
false
none
Adv information
advertiser
AdvertiserVo
false
none
Adv publisher information
AdTradeMethodResp
{ 
  "iconUrlColor": "string", 
  "identifier": "string", 
  "payAccount": "string", 
  "payBank": "string", 
  "payId": 0, 
  "paySubBank": "string", 
  "payType": "string", 
  "tradeMethodName": "string" 
} 
 
AdTradeMethodResp
42.18. Properties
Name
Type
Required
Restrictions
Description
iconUrlColor
string
false
none
Icon URL with background color
identifier
string
false
none
Identifier of trade method. Eg: AliPay, Visa
payAccount
string
false
none
Payment method account number
payBank
string
false
none
Bank information for bank-based payment methods
payId
integer(int64)
false
none
Transaction method ID, i.e., user payment method ID, available for sale type ads
paySubBank
string
false
none
Sub-branch information for bank-based payment methods
payType
string
false
none
Payment method, e.g.: BANK, WECHAT
tradeMethodName
string
false
none
Trade method display name
AdUpdateReq
{ 
  "advNo": "string", 
  "advStatus": 0, 
  "asset": "string", 
  "authType": "FIDO2", 
  "autoReplyMsg": "string", 
  "buyerBtcPositionLimit": 0, 
  "buyerKycLimit": 0, 
  "buyerRegDaysLimit": 0, 
  "code": "string", 
  "emailVerifyCode": "string", 
  "fiatUnit": "string", 
  "googleVerifyCode": "string", 
  "initAmount": 0, 
  "maxSingleTransAmount": 0, 
  "minSingleTransAmount": 0, 
  "mobileVerifyCode": "string", 
  "payTimeLimit": 0, 
  "price": 0, 
  "priceFloatingRatio": 0, 
  "priceType": 0, 
  "rateFloatingRatio": 0, 
  "remarks": "string", 
  "saveAsTemplate": 0, 


---

## Page 41

sapi-v7.4.md
2024-05-08
41 / 419
  "takerAdditionalKycRequired": 0, 
  "templateName": "string", 
  "tradeMethods": [ 
    { 
      "identifier": "string", 
      "payId": 0, 
      "payType": "string" 
    } 
  ], 
  "tradeType": "string", 
  "updateMode": "string", 
  "userAllTradeCountMax": 0, 
  "userAllTradeCountMin": 0, 
  "userBuyTradeCountMax": 0, 
  "userBuyTradeCountMin": 0, 
  "userSellTradeCountMax": 0, 
  "userSellTradeCountMin": 0, 
  "userTradeCompleteCountMin": 0, 
  "userTradeCompleteRateFilterTime": 0, 
  "userTradeCompleteRateMin": 0, 
  "userTradeCountFilterTime": 0, 
  "userTradeType": 0, 
  "userTradeVolumeAsset": "string", 
  "userTradeVolumeFilterTime": 0, 
  "userTradeVolumeMax": 0, 
  "userTradeVolumeMin": 0, 
  "yubikeyVerifyCode": "string" 
} 
 
AdUpdateReq
42.19. Properties
Name
Type
Required
Restrictions
Description
advNo
string
true
none
Adv number
advStatus
integer(int32)
false
none
Adv status， 1: Online，3: Offline，4ÏClosed
asset
string
false
none
Crypto asset: BTC
authType
string
false
none
Authenticate code type: GOOGLE
autoReplyMsg
string
false
none
Auto reply message
buyerBtcPositionLimit
number
false
none
Require buyer minimum BTC asset position
buyerKycLimit
integer(int32)
false
none
Require buyer kyc verified. 0: No, 1: Yes
buyerRegDaysLimit
integer(int32)
false
none
Require buyer minimum registered day. 0: No, 1: Yes
code
string
false
none
Authenticate Code
emailVerifyCode
string
false
none
Email verification code
fiatUnit
string
false
none
Fiat currency: CNY
googleVerifyCode
string
false
none
Google verification code
initAmount
number
false
none
Adv amount
maxSingleTransAmount
number
false
none
Single transaction maximum amount in fiat
minSingleTransAmount
number
false
none
Single transaction minimum amount in fiat
mobileVerifyCode
string
false
none
Mobile verification code
payTimeLimit
integer(int32)
false
none
Maximum time waiting for payment in minute
price
number
false
none
Adv price
priceFloatingRatio
number
false
none
Floating price ratio of the adv
priceType
integer(int32)
false
none
Adv price type. 1: FIXED, 2: FLOATING
rateFloatingRatio
number
false
none
Exchange rate ration of the trading pair
remarks
string
false
none
Remark
saveAsTemplate
integer(int32)
false
none
Adv as template. 0: No, 1: Yes
takerAdditionalKycRequired
integer(int32)
false
none
whether taker additional kyc required: 0 not required 1 required


---

## Page 42

sapi-v7.4.md
2024-05-08
42 / 419
Name
Type
Required
Restrictions
Description
templateName
string
false
none
Template name
tradeMethods
[AdsTradeMethodVo]
false
none
List of accepted payment method for the adv
tradeType
string
false
none
Adv trade type. 0: BUY, 1: SELL
updateMode
string
false
none
Update mode - default [selective]，selective：Only update presenting
fields, full：if field not present -> update to NULL, quickedit: support
partial fields.
userAllTradeCountMax
integer(int32)
false
none
Require user maximum all trades
userAllTradeCountMin
integer(int32)
false
none
Require user minimum all trades
userBuyTradeCountMax
integer(int32)
false
none
Require user maximum buy trades
userBuyTradeCountMin
integer(int32)
false
none
Require user minimum buy trades
userSellTradeCountMax
integer(int32)
false
none
Require user maximum sell trades
userSellTradeCountMin
integer(int32)
false
none
Require user minimum sell trades
userTradeCompleteCountMin
integer(int32)
false
none
Require user minimum completed trades
userTradeCompleteRateFilterTime
integer(int32)
false
none
Filter user completion rate type. 1: Last 30D, 2: All-time
userTradeCompleteRateMin
number
false
none
Require user minimum completion rate
userTradeCountFilterTime
integer(int32)
false
none
Filter user trade count type. 1: Last 30D, 2: All-time
userTradeType
integer(int32)
false
none
User trade volume tradeType. 0: BUY, 1: SELL, 2: ALL
userTradeVolumeAsset
string
false
none
User trade volume asset for requirement
userTradeVolumeFilterTime
integer(int32)
false
none
Filter user trade volume. 1: Last 30D, 2: All-time
userTradeVolumeMax
number
false
none
Require user maximum trade volume
userTradeVolumeMin
number
false
none
Require user minimum trade volume
yubikeyVerifyCode
string
false
none
Yubikey verification code
42.19.1. Enumerated Values
Property
Value
authType
FIDO2
authType
FUND_PWD
authType
GOOGLE
authType
SMS
AdUpdateStatusResp
{ 
  "failList": [ 
    { 
      "advNo": "string", 
      "errorCode": "string", 
      "errorMsg": "string" 
    } 
  ], 
  "status": true 
} 
 
AdUpdateStatusResp
42.20. Properties
Name
Type
Required
Restrictions
Description
failList
[StatusUpdateResult]
false
none
List of failed result
status
boolean
false
none
Update result, true or false
AdVisibleRetVo


---

## Page 43

sapi-v7.4.md
2024-05-08
43 / 419
{ 
  "freeAmountVisible": 0, 
  "orderFlowVisible": 0, 
  "surplusAmountVisible": 0, 
  "userSetVisible": 0 
} 
 
AdVisibleRetVo
42.21. Properties
Name
Type
Required
Restrictions
Description
freeAmountVisible
integer(int32)
false
none
User funding wallet sufficient visibility. (0: Invisible, 1: Visible)
orderFlowVisible
integer(int32)
false
none
Order business visibility. (0: Invisible, 1: Visible)
surplusAmountVisible
integer(int32)
false
none
Remaining quantity visibility. (0: Invisible, 1: Visible)
userSetVisible
integer(int32)
false
none
User set visibility. (0: Invisible, 1: Visible)
AdjustMarginBarResp
{ 
  "success": true 
} 
 
AdjustMarginBarResp
42.22. Properties
Name
Type
Required
Restrictions
Description
success
boolean
false
none
none
AdsTradeMethodVo
{ 
  "identifier": "string", 
  "payId": 0, 
  "payType": "string" 
} 
 
AdsTradeMethodVo
42.23. Properties
Name
Type
Required
Restrictions
Description
identifier
string
false
none
Identifier of trade method. Eg: AliPay, Visa
payId
integer(int64)
false
none
User trade method ID.
payType
string
false
none
Deprecated. Please use identifier.
AdvertiserVo
{ 
  "advConfirmTime": 0, 
  "email": "string", 
  "margin": 0, 
  "marginUnit": "string", 
  "mobile": "string", 
  "monthFinishRate": 0, 
  "monthOrderCount": 0, 
  "nickName": "string", 
  "orderCount": 0, 
  "realName": "string", 
  "registrationTime": "2019-08-24T14:15:22Z", 
  "tagIconUrls": [ 


---

## Page 44

sapi-v7.4.md
2024-05-08
44 / 419
    "string" 
  ], 
  "userNo": "string", 
  "userType": "string" 
} 
 
AdvertiserVo
42.24. Properties
Name
Type
Required
Restrictions
Description
advConfirmTime
integer(int32)
false
none
Average release time (second)
email
string
false
none
Email
margin
number
false
none
Margin amount
marginUnit
string
false
none
Margin unit, e.g. BNB
mobile
string
false
none
none
monthFinishRate
number
false
none
30-day completion rate
monthOrderCount
integer(int32)
false
none
30-day transaction volume
nickName
string
false
none
User nickname
orderCount
integer(int32)
false
none
Total transaction volume
realName
string
false
none
User real name
registrationTime
string(date-time)
false
none
none
tagIconUrls
[string]
false
none
User tag icon URL list
userNo
string
false
none
User number string
userType
string
false
none
User type (merchant, user)
AllForceOrderDto
{ 
  "averagePrice": 0, 
  "executedQty": 0, 
  "orderTime": 0, 
  "origQty": 0, 
  "price": 0, 
  "side": "BUY", 
  "status": "string", 
  "symbol": "string", 
  "timeInForce": "FOK", 
  "type": "string", 
  "updatedTime": 0 
} 
 
AllForceOrderDto
42.25. Properties
Name
Type
Required
Restrictions
Description
averagePrice
number
false
none
平均价格
executedQty
number
false
none
成交amount
orderTime
integer(int64)
false
none
订单时间戳
origQty
number
false
none
订单amount
price
number
false
none
订单价格
side
string
false
none
交易⽅向
status
string
false
none
状态
symbol
string
false
none
交易对
timeInForce
string
false
none
挂单策略


---

## Page 45

sapi-v7.4.md
2024-05-08
45 / 419
Name
Type
Required
Restrictions
Description
type
string
false
none
类型
updatedTime
integer(int64)
false
none
更新时间
42.25.1. Enumerated Values
Property
Value
side
BUY
side
SELL
timeInForce
FOK
timeInForce
GTC
timeInForce
IOC
ApiAgentKickbackResp
{ 
  "asset": "string", 
  "income": "string", 
  "symbol": "string", 
  "time": 0 
} 
 
ApiAgentKickbackResp
42.26. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
income
string
false
none
none
symbol
string
false
none
none
time
integer(int64)
false
none
none
ApiAuthorityResp
{ 
  "createTime": "2019-08-24T14:15:22Z", 
  "enableFutures": true, 
  "enableInternalTransfer": true, 
  "enableMargin": true, 
  "enablePortfolioMarginTrading": true, 
  "enableReading": true, 
  "enableSpotAndMarginTrading": true, 
  "enableVanillaOptions": true, 
  "enableWithdrawals": true, 
  "ipRestrict": true, 
  "permitsUniversalTransfer": true, 
  "tradingAuthorityExpirationTime": "2019-08-24T14:15:22Z" 
} 
 
ApiAuthorityResp
42.27. Properties
Name
Type
Required
Restrictions
Description
createTime
string(date-time)
false
none
none
enableFutures
boolean
false
none
none
enableInternalTransfer
boolean
false
none
none
enableMargin
boolean
false
none
none
enablePortfolioMarginTrading
boolean
false
none
none


---

## Page 46

sapi-v7.4.md
2024-05-08
46 / 419
Name
Type
Required
Restrictions
Description
enableReading
boolean
false
none
none
enableSpotAndMarginTrading
boolean
false
none
none
enableVanillaOptions
boolean
false
none
none
enableWithdrawals
boolean
false
none
none
ipRestrict
boolean
false
none
none
permitsUniversalTransfer
boolean
false
none
none
tradingAuthorityExpirationTime
string(date-time)
false
none
none
ApiKeyInfoResp
{ 
  "apiKey": "string", 
  "apiName": "string", 
  "ip": "string", 
  "type": "string" 
} 
 
ApiKeyInfoResp
42.28. Properties
Name
Type
Required
Restrictions
Description
apiKey
string
false
none
none
apiName
string
false
none
none
ip
string
false
none
none
type
string
false
none
none
ApiModelResp
{ 
  "apiKey": "string", 
  "secretKey": "string", 
  "type": "string" 
} 
 
ApiModelResp
42.29. Properties
Name
Type
Required
Restrictions
Description
apiKey
string
false
none
none
secretKey
string
false
none
none
type
string
false
none
none
ApplyWithdrawResp
{ 
  "id": "string" 
} 
 
ApplyWithdrawResp
42.30. Properties
Name
Type
Required
Restrictions
Description
id
string
false
none
none


---

## Page 47

sapi-v7.4.md
2024-05-08
47 / 419
AssetAllocation
{ 
  "allocation": 0, 
  "targetAsset": "string" 
} 
 
AssetAllocation
42.31. Properties
Name
Type
Required
Restrictions
Description
allocation
integer(int32)
false
none
none
targetAsset
string
false
none
none
AssetConfig
{ 
  "maxAdd": 0, 
  "maxSwap": 0, 
  "minAdd": 0, 
  "minSwap": 0 
} 
 
AssetConfig
42.32. Properties
Name
Type
Required
Restrictions
Description
maxAdd
number
false
none
none
maxSwap
number
false
none
none
minAdd
number
false
none
none
minSwap
number
false
none
none
AssetLeverageResp
{ 
  "asset": "string", 
  "leverage": 0 
} 
 
AssetLeverageResp
42.33. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
leverage
integer(int32)
false
none
none
AutoInvestAddPlanResp
{ 
  "nextExecutionDateTime": 0, 
  "planId": 0 
} 
 
AutoInvestAddPlanResp
42.34. Properties


---

## Page 48

sapi-v7.4.md
2024-05-08
48 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
nextExecutionDateTime
integer(int64)
false
none
next execution DateTime
planId
integer(int64)
false
none
planId
AutoInvestAllAssetResp
{ 
  "sourceAssets": [ 
    "string" 
  ], 
  "targetAssets": [ 
    "string" 
  ] 
} 
 
AutoInvestAllAssetResp
42.35. Properties
Name
Type
Required
Restrictions
Description
sourceAssets
[string]
false
none
targetAssets
targetAssets
[string]
false
none
targetAssets
AutoInvestAssetDetailResp
{ 
  "roiAndDimensionTypeList": [ 
    { 
      "dimensionUnit": "string", 
      "dimensionValue": 0, 
      "simulateRoi": 0 
    } 
  ], 
  "targetAsset": "string" 
} 
 
AutoInvestAssetDetailResp
42.36. Properties
Name
Type
Required
Restrictions
Description
roiAndDimensionTypeList
[AutoInvestRoiAndDimensionTypeResp]
false
none
none
targetAsset
string
false
none
target asset
AutoInvestEditPlanResp
{ 
  "nextExecutionDateTime": 0, 
  "planId": 0 
} 
 
AutoInvestEditPlanResp
42.37. Properties
Name
Type
Required
Restrictions
Description
nextExecutionDateTime
integer(int64)
false
none
next execution DateTime
planId
integer(int64)
false
none
planId
AutoInvestEditPlanStatusResp


---

## Page 49

sapi-v7.4.md
2024-05-08
49 / 419
{ 
  "nextExecutionDateTime": 0, 
  "planId": 0, 
  "status": "string" 
} 
 
AutoInvestEditPlanStatusResp
42.38. Properties
Name
Type
Required
Restrictions
Description
nextExecutionDateTime
integer(int64)
false
none
next execution DateTime
planId
integer(int64)
false
none
planId
status
string
false
none
plan status
AutoInvestHistoryResp
{ 
  "executionPrice": 0, 
  "executionType": "string", 
  "failedType": "string", 
  "flexibleUsed": true, 
  "id": 0, 
  "planId": 0, 
  "planName": "string", 
  "planType": "string", 
  "sourceAsset": "string", 
  "sourceAssetAmount": 0, 
  "sourceWallet": "string", 
  "subscriptionCycle": "string", 
  "targetAsset": "string", 
  "targetAssetAmount": 0, 
  "transactionDateTime": 0, 
  "transactionFee": 0, 
  "transactionFeeUnit": "string", 
  "transactionStatus": "string" 
} 
 
AutoInvestHistoryResp
42.39. Properties
Name
Type
Required
Restrictions
Description
executionPrice
number
false
none
none
executionType
string
false
none
none
failedType
string
false
none
none
flexibleUsed
boolean
false
none
none
id
integer(int64)
false
none
none
planId
integer(int64)
false
none
none
planName
string
false
none
none
planType
string
false
none
none
sourceAsset
string
false
none
none
sourceAssetAmount
number
false
none
none
sourceWallet
string
false
none
none
subscriptionCycle
string
false
none
none
targetAsset
string
false
none
none
targetAssetAmount
number
false
none
none
transactionDateTime
integer(int64)
false
none
none
transactionFee
number
false
none
none


---

## Page 50

sapi-v7.4.md
2024-05-08
50 / 419
Name
Type
Required
Restrictions
Description
transactionFeeUnit
string
false
none
none
transactionStatus
string
false
none
none
AutoInvestIndexInfoResp
{ 
  "assetAllocation": [ 
    { 
      "allocation": 0, 
      "targetAsset": "string" 
    } 
  ], 
  "indexId": 0, 
  "indexName": "string", 
  "status": "PAUSED" 
} 
 
AutoInvestIndexInfoResp
42.40. Properties
Name
Type
Required
Restrictions
Description
assetAllocation
[AssetAllocation]
false
none
none
indexId
integer(int64)
false
none
none
indexName
string
false
none
none
status
string
false
none
status RUNNING/REBALANCING/PAUSED
42.40.1. Enumerated Values
Property
Value
status
PAUSED
status
REBALANCING
status
RUNNING
AutoInvestIndexUserIndexSummaryResp
{ 
  "assetAllocation": [ 
    { 
      "allocation": 0, 
      "targetAsset": "string" 
    } 
  ], 
  "currentInvestedInUSD": 0, 
  "details": [ 
    { 
      "apr": 0, 
      "asset": "string", 
      "canPurchase": true, 
      "duration": 0, 
      "extraRewardAPR": 0, 
      "extraRewardAsset": "string", 
      "isSoldOut": true, 
      "renewable": true, 
      "rewardAsset": "string", 
      "status": "string", 
      "subscriptionStartTime": 0 
    } 
  ], 
  "indexId": 0, 
  "pnlInUSD": 0, 
  "roi": 0, 
  "totalInvestedInUSD": 0 
} 
 


---

## Page 51

sapi-v7.4.md
2024-05-08
51 / 419
AutoInvestIndexUserIndexSummaryResp
42.41. Properties
Name
Type
Required
Restrictions
Description
assetAllocation
[AssetAllocation]
false
none
none
currentInvestedInUSD
number
false
none
none
details
[Detail]
false
none
none
indexId
integer(int64)
false
none
none
pnlInUSD
number
false
none
none
roi
number
false
none
none
totalInvestedInUSD
number
false
none
none
AutoInvestOneOffResp
{ 
  "transactionId": 0, 
  "waitSecond": 0 
} 
 
AutoInvestOneOffResp
42.42. Properties
Name
Type
Required
Restrictions
Description
transactionId
integer(int64)
false
none
transactionId
waitSecond
integer(int32)
false
none
waitSecond
AutoInvestOneOffStatusResp
{ 
  "status": "CONVERTING", 
  "transactionId": 0 
} 
 
AutoInvestOneOffStatusResp
42.43. Properties
Name
Type
Required
Restrictions
Description
status
string
false
none
none
transactionId
integer(int64)
false
none
none
42.43.1. Enumerated Values
Property
Value
status
CONVERTING
status
FAILED
status
PENDING
status
START_DEDUCE_FROM_CONVERT_ACCOUNT
status
SUCCESS
AutoInvestPlanListResp
{ 
  "planValueInBTC": 0, 
  "planValueInUSD": 0, 
  "plans": [ 


---

## Page 52

sapi-v7.4.md
2024-05-08
52 / 419
    { 
      "creationDateTime": 0, 
      "details": [ 
        { 
          "assetStatus": "string", 
          "assetValueInUSD": 0, 
          "availableAmount": 0, 
          "availableAmountUnit": "string", 
          "averagePriceInUSD": 0, 
          "percentage": 0, 
          "pnlInUSD": 0, 
          "purchasedAmount": 0, 
          "purchasedAmountUnit": "string", 
          "redeemedAmout": 0, 
          "redeemedAmoutUnit": "string", 
          "roi": 0, 
          "targetAsset": "string", 
          "totalInvestedInUSD": 0 
        } 
      ], 
      "editAllowed": true, 
      "firstExecutionDateTime": 0, 
      "flexibleAllowedToUse": true, 
      "lastUpdatedDateTime": 0, 
      "nextExecutionDateTime": 0, 
      "planId": 0, 
      "planType": "string", 
      "planValueInUSD": 0, 
      "pnlInUSD": 0, 
      "roi": 0, 
      "sourceAsset": "string", 
      "sourceWallet": "string", 
      "status": "string", 
      "subscriptionAmount": 0, 
      "subscriptionCycle": "string", 
      "subscriptionStartDay": 0, 
      "subscriptionStartTime": 0, 
      "subscriptionStartWeekday": "string", 
      "targetAsset": "string", 
      "totalInvestedInUSD": 0, 
      "totalTargetAmount": 0 
    } 
  ], 
  "pnlInUSD": 0, 
  "roi": 0 
} 
 
AutoInvestPlanListResp
42.44. Properties
Name
Type
Required
Restrictions
Description
planValueInBTC
number
false
none
plan Value In BTC
planValueInUSD
number
false
none
plan Value In USD
plans
[AutoInvestPlanResp]
false
none
none
pnlInUSD
number
false
none
pnl Value In USD
roi
number
false
none
none
AutoInvestPlanResp
{ 
  "creationDateTime": 0, 
  "details": [ 
    { 
      "assetStatus": "string", 
      "assetValueInUSD": 0, 
      "availableAmount": 0, 
      "availableAmountUnit": "string", 
      "averagePriceInUSD": 0, 
      "percentage": 0, 
      "pnlInUSD": 0, 
      "purchasedAmount": 0, 
      "purchasedAmountUnit": "string", 


---

## Page 53

sapi-v7.4.md
2024-05-08
53 / 419
      "redeemedAmout": 0, 
      "redeemedAmoutUnit": "string", 
      "roi": 0, 
      "targetAsset": "string", 
      "totalInvestedInUSD": 0 
    } 
  ], 
  "editAllowed": true, 
  "firstExecutionDateTime": 0, 
  "flexibleAllowedToUse": true, 
  "lastUpdatedDateTime": 0, 
  "nextExecutionDateTime": 0, 
  "planId": 0, 
  "planType": "string", 
  "planValueInUSD": 0, 
  "pnlInUSD": 0, 
  "roi": 0, 
  "sourceAsset": "string", 
  "sourceWallet": "string", 
  "status": "string", 
  "subscriptionAmount": 0, 
  "subscriptionCycle": "string", 
  "subscriptionStartDay": 0, 
  "subscriptionStartTime": 0, 
  "subscriptionStartWeekday": "string", 
  "targetAsset": "string", 
  "totalInvestedInUSD": 0, 
  "totalTargetAmount": 0 
} 
 
AutoInvestPlanResp
42.45. Properties
Name
Type
Required
Restrictions
Description
creationDateTime
integer(int64)
false
none
none
details
[AutoInvestPortfolioDetailResp]
false
none
none
editAllowed
boolean
false
none
none
firstExecutionDateTime
integer(int64)
false
none
none
flexibleAllowedToUse
boolean
false
none
none
lastUpdatedDateTime
integer(int64)
false
none
none
nextExecutionDateTime
integer(int64)
false
none
none
planId
integer(int64)
false
none
planId
planType
string
false
none
planType. SINGLE/PORTFOLIO/INDEX
planValueInUSD
number
false
none
none
pnlInUSD
number
false
none
none
roi
number
false
none
none
sourceAsset
string
false
none
none
sourceWallet
string
false
none
none
status
string
false
none
status. ONGOING/PAUSED/REMOVED
subscriptionAmount
number
false
none
none
subscriptionCycle
string
false
none
none
subscriptionStartDay
integer(int32)
false
none
none
subscriptionStartTime
integer(int32)
false
none
none
subscriptionStartWeekday
string
false
none
none
targetAsset
string
false
none
none
totalInvestedInUSD
number
false
none
none
totalTargetAmount
number
false
none
none
AutoInvestPortfolioDetailResp


---

## Page 54

sapi-v7.4.md
2024-05-08
54 / 419
{ 
  "assetStatus": "string", 
  "assetValueInUSD": 0, 
  "availableAmount": 0, 
  "availableAmountUnit": "string", 
  "averagePriceInUSD": 0, 
  "percentage": 0, 
  "pnlInUSD": 0, 
  "purchasedAmount": 0, 
  "purchasedAmountUnit": "string", 
  "redeemedAmout": 0, 
  "redeemedAmoutUnit": "string", 
  "roi": 0, 
  "targetAsset": "string", 
  "totalInvestedInUSD": 0 
} 
 
AutoInvestPortfolioDetailResp
42.46. Properties
Name
Type
Required
Restrictions
Description
assetStatus
string
false
none
none
assetValueInUSD
number
false
none
none
availableAmount
number
false
none
none
availableAmountUnit
string
false
none
none
averagePriceInUSD
number
false
none
none
percentage
integer(int32)
false
none
none
pnlInUSD
number
false
none
none
purchasedAmount
number
false
none
none
purchasedAmountUnit
string
false
none
none
redeemedAmout
number
false
none
none
redeemedAmoutUnit
string
false
none
none
roi
number
false
none
none
targetAsset
string
false
none
none
totalInvestedInUSD
number
false
none
none
AutoInvestRebalanceHistoryResp
{ 
  "indexId": 0, 
  "indexName": "string", 
  "rebalanceFee": 0, 
  "rebalanceFeeUnit": "string", 
  "rebalanceId": 0, 
  "status": "INIT", 
  "transactionDetails": [ 
    { 
      "asset": "string", 
      "rebalanceAmount": 0, 
      "rebalanceDirection": "BUY", 
      "transactionDateTime": 0 
    } 
  ] 
} 
 
AutoInvestRebalanceHistoryResp
42.47. Properties
Name
Type
Required
Restrictions
Description
indexId
integer(int64)
false
none
none


---

## Page 55

sapi-v7.4.md
2024-05-08
55 / 419
Name
Type
Required
Restrictions
Description
indexName
string
false
none
none
rebalanceFee
number
false
none
none
rebalanceFeeUnit
string
false
none
none
rebalanceId
integer(int64)
false
none
none
status
string
false
none
status INIT/SUCCESS
transactionDetails
[TransactionDetail]
false
none
none
42.47.1. Enumerated Values
Property
Value
status
INIT
status
SUCCESS
AutoInvestRedeemResp
{ 
  "redemptionId": 0 
} 
 
AutoInvestRedeemResp
42.48. Properties
Name
Type
Required
Restrictions
Description
redemptionId
integer(int64)
false
none
redemptionId
AutoInvestRedemptionHistoryResp
{ 
  "amount": 0, 
  "asset": "string", 
  "indexId": 0, 
  "indexName": "string", 
  "redemptionDateTime": 0, 
  "redemptionId": 0, 
  "status": "FAILED", 
  "transactionFee": 0, 
  "transactionFeeUnit": "string" 
} 
 
AutoInvestRedemptionHistoryResp
42.49. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
indexId
integer(int64)
false
none
none
indexName
string
false
none
none
redemptionDateTime
integer(int64)
false
none
none
redemptionId
integer(int64)
false
none
none
status
string
false
none
status INIT/SUCCESS/FAILED
transactionFee
number
false
none
none
transactionFeeUnit
string
false
none
none
42.49.1. Enumerated Values


---

## Page 56

sapi-v7.4.md
2024-05-08
56 / 419
Property
Value
Property
Value
status
FAILED
status
INIT
status
SUCCESS
AutoInvestRoiAndDimensionTypeResp
{ 
  "dimensionUnit": "string", 
  "dimensionValue": 0, 
  "simulateRoi": 0 
} 
 
AutoInvestRoiAndDimensionTypeResp
42.50. Properties
Name
Type
Required
Restrictions
Description
dimensionUnit
string
false
none
simulate unit,(year, month, day)
dimensionValue
integer(int32)
false
none
dimension value
simulateRoi
number
false
none
simulate roi
AutoInvestSourceAssetDetailResp
{ 
  "assetMaxAmount": 0, 
  "assetMinAmount": 0, 
  "flexibleAmount": 0, 
  "scale": 0, 
  "sourceAsset": "string" 
} 
 
AutoInvestSourceAssetDetailResp
42.51. Properties
Name
Type
Required
Restrictions
Description
assetMaxAmount
number
false
none
asset max amount
assetMinAmount
number
false
none
asset min amount
flexibleAmount
number
false
none
flexible amount
scale
integer(int32)
false
none
scale
sourceAsset
string
false
none
source asset
AutoInvestSourceAssetResp
{ 
  "feeRate": 0, 
  "sourceAssets": [ 
    { 
      "assetMaxAmount": 0, 
      "assetMinAmount": 0, 
      "flexibleAmount": 0, 
      "scale": 0, 
      "sourceAsset": "string" 
    } 
  ], 
  "taxRate": 0 
} 
 
AutoInvestSourceAssetResp


---

## Page 57

sapi-v7.4.md
2024-05-08
57 / 419
42.52. Properties
Name
Type
Required
Restrictions
Description
feeRate
number
false
none
fee rate
sourceAssets
[AutoInvestSourceAssetDetailResp]
false
none
target assets with roi info
taxRate
number
false
none
tax rate
AutoInvestTargetAssetResp
{ 
  "autoInvestAssetList": [ 
    { 
      "roiAndDimensionTypeList": [ 
        { 
          "dimensionUnit": "string", 
          "dimensionValue": 0, 
          "simulateRoi": 0 
        } 
      ], 
      "targetAsset": "string" 
    } 
  ], 
  "targetAssets": [ 
    "string" 
  ] 
} 
 
AutoInvestTargetAssetResp
42.53. Properties
Name
Type
Required
Restrictions
Description
autoInvestAssetList
[AutoInvestAssetDetailResp]
false
none
target assets with roi info
targetAssets
[string]
false
none
all can invest target assets
AutoInvestTargetAssetRoiResp
{ 
  "date": 0, 
  "simulateRoi": 0 
} 
 
AutoInvestTargetAssetRoiResp
42.54. Properties
Name
Type
Required
Restrictions
Description
date
integer(int64)
false
none
calc Date
simulateRoi
number
false
none
roi
AutoSubscriptionResp
{ 
  "success": true 
} 
 
AutoSubscriptionResp
42.55. Properties
Name
Type
Required
Restrictions
Description
success
boolean
false
none
none


---

## Page 58

sapi-v7.4.md
2024-05-08
58 / 419
BasketDetailApiVo
{ 
  "amount": 0, 
  "notionalValue": 0, 
  "symbol": "string" 
} 
 
BasketDetailApiVo
42.56. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
notionalValue
number
false
none
none
symbol
string
false
none
none
BatchCreateOrderReq
{ 
  "cancelExistingOrder": true, 
  "clientOrderId": "string", 
  "price": 0, 
  "quantity": 0, 
  "side": "BUY", 
  "symbol": "string", 
  "timeInforce": "string" 
} 
 
BatchCreateOrderReq
42.57. Properties
Name
Type
Required
Restrictions
Description
cancelExistingOrder
boolean
false
none
none
clientOrderId
string
false
none
none
price
number
false
none
none
quantity
number
false
none
none
side
string
false
none
none
symbol
string
false
none
none
timeInforce
string
false
none
none
42.57.1. Enumerated Values
Property
Value
side
BUY
side
SELL
BlvtRedeemRecordResp
{ 
  "amount": "string", 
  "fee": "string", 
  "id": 0, 
  "nav": "string", 
  "netProceed": "string", 
  "timestamp": 0, 
  "tokenName": "string" 
} 
 


---

## Page 59

sapi-v7.4.md
2024-05-08
59 / 419
BlvtRedeemRecordResp
42.58. Properties
Name
Type
Required
Restrictions
Description
amount
string
false
none
none
fee
string
false
none
none
id
integer(int64)
false
none
none
nav
string
false
none
none
netProceed
string
false
none
none
timestamp
integer(int64)
false
none
none
tokenName
string
false
none
none
BlvtRedeemResp
{ 
  "amount": "string", 
  "id": 0, 
  "redeemAmount": "string", 
  "status": "string", 
  "timestamp": 0, 
  "tokenName": "string" 
} 
 
BlvtRedeemResp
42.59. Properties
Name
Type
Required
Restrictions
Description
amount
string
false
none
none
id
integer(int64)
false
none
none
redeemAmount
string
false
none
none
status
string
false
none
none
timestamp
integer(int64)
false
none
none
tokenName
string
false
none
none
BlvtSubscribeRecordResp
{ 
  "amount": "string", 
  "fee": "string", 
  "id": 0, 
  "nav": "string", 
  "timestamp": 0, 
  "tokenName": "string", 
  "totalcharge": "string" 
} 
 
BlvtSubscribeRecordResp
42.60. Properties
Name
Type
Required
Restrictions
Description
amount
string
false
none
none
fee
string
false
none
none
id
integer(int64)
false
none
none
nav
string
false
none
none
timestamp
integer(int64)
false
none
none


---

## Page 60

sapi-v7.4.md
2024-05-08
60 / 419
Name
Type
Required
Restrictions
Description
tokenName
string
false
none
none
totalcharge
string
false
none
none
BlvtSubscribeResp
{ 
  "amount": "string", 
  "cost": "string", 
  "id": 0, 
  "status": "string", 
  "timestamp": 0, 
  "tokenName": "string" 
} 
 
BlvtSubscribeResp
42.61. Properties
Name
Type
Required
Restrictions
Description
amount
string
false
none
none
cost
string
false
none
none
id
integer(int64)
false
none
none
status
string
false
none
none
timestamp
integer(int64)
false
none
none
tokenName
string
false
none
none
BlvtTokenInfoResp
{ 
  "basket": "string", 
  "currentBaskets": [ 
    { 
      "amount": 0, 
      "notionalValue": 0, 
      "symbol": "string" 
    } 
  ], 
  "dailyManagementFee": "string", 
  "dailyPurchaseLimit": "string", 
  "dailyRedeemLimit": "string", 
  "description": "string", 
  "fundingRate": "string", 
  "nav": "string", 
  "purchaseFeePct": "string", 
  "realLeverage": "string", 
  "redeemFeePct": "string", 
  "timestamp": 0, 
  "tokenIssued": "string", 
  "tokenName": "string", 
  "underlying": "string" 
} 
 
BlvtTokenInfoResp
42.62. Properties
Name
Type
Required
Restrictions
Description
basket
string
false
none
none
currentBaskets
[BasketDetailApiVo]
false
none
none
dailyManagementFee
string
false
none
none
dailyPurchaseLimit
string
false
none
none


---

## Page 61

sapi-v7.4.md
2024-05-08
61 / 419
Name
Type
Required
Restrictions
Description
dailyRedeemLimit
string
false
none
none
description
string
false
none
none
fundingRate
string
false
none
none
nav
string
false
none
none
purchaseFeePct
string
false
none
none
realLeverage
string
false
none
none
redeemFeePct
string
false
none
none
timestamp
integer(int64)
false
none
none
tokenIssued
string
false
none
none
tokenName
string
false
none
none
underlying
string
false
none
none
BlvtUserConfigResp
{ 
  "tokenName": "string", 
  "userDailyTotalPurchaseLimit": "string", 
  "userDailyTotalRedeemLimit": "string" 
} 
 
BlvtUserConfigResp
42.63. Properties
Name
Type
Required
Restrictions
Description
tokenName
string
false
none
none
userDailyTotalPurchaseLimit
string
false
none
none
userDailyTotalRedeemLimit
string
false
none
none
BorrowRepayHistoryResp
{ 
  "amount": 0, 
  "asset": "string", 
  "clientTag": "string", 
  "interest": 0, 
  "isolatedSymbol": "string", 
  "principal": 0, 
  "status": "string", 
  "timestamp": 0, 
  "txId": 0 
} 
 
BorrowRepayHistoryResp
42.64. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
还款⾦额
asset
string
false
none
资⾦名称
clientTag
string
false
none
客户标记
interest
number
false
none
偿还利息
isolatedSymbol
string
false
none
逐仓symbol
principal
number
false
none
偿还本⾦
status
string
false
none
状态


---

## Page 62

sapi-v7.4.md
2024-05-08
62 / 419
Name
Type
Required
Restrictions
Description
timestamp
integer(int64)
false
none
还款时间
txId
integer(int64)
false
none
交易流⽔号
BorrowableResp
{ 
  "amount": 0, 
  "borrowLimit": 0 
} 
 
BorrowableResp
42.65. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
borrowLimit
number
false
none
none
BrokerAssetFreezeResponse
{ 
  "clientTransId": "string", 
  "errorMessage": "string", 
  "status": "FAILURE", 
  "tranId": 0 
} 
 
BrokerAssetFreezeResponse
42.66. Properties
Name
Type
Required
Restrictions
Description
clientTransId
string
false
none
三⽅的交易id，必须唯⼀
errorMessage
string
false
none
错误信息
status
string
false
none
状态
tranId
integer(int64)
false
none
tranId
42.66.1. Enumerated Values
Property
Value
status
FAILURE
status
INIT
status
PROCESS
status
SUCCESS
BrokerAssetUnfreezeResponse
{ 
  "clientTransId": "string", 
  "errorMessage": "string", 
  "status": "FAILURE", 
  "tranId": 0 
} 
 
BrokerAssetUnfreezeResponse
42.67. Properties


---

## Page 63

sapi-v7.4.md
2024-05-08
63 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
clientTransId
string
false
none
三⽅的交易id，必须唯⼀
errorMessage
string
false
none
错误信息
status
string
false
none
状态
tranId
integer(int64)
false
none
tranId
42.67.1. Enumerated Values
Property
Value
status
FAILURE
status
INIT
status
PROCESS
status
SUCCESS
BrokerBnbBurnSwitchResp
{ 
  "spotBNBBurn": true, 
  "subAccountId": 0 
} 
 
BrokerBnbBurnSwitchResp
42.68. Properties
Name
Type
Required
Restrictions
Description
spotBNBBurn
boolean
false
none
spotBNBBurn
subAccountId
integer(int64)
true
none
经销商⼦账户id
BrokerCommissionFuturesResponse
{ 
  "makerAdjustment": 0, 
  "makerCommission": 0, 
  "subAccountId": 0, 
  "symbol": "string", 
  "takerAdjustment": 0, 
  "takerCommission": 0 
} 
 
BrokerCommissionFuturesResponse
42.69. Properties
Name
Type
Required
Restrictions
Description
makerAdjustment
integer(int32)
false
none
makerAdjustment
makerCommission
integer(int32)
false
none
makerCommission
subAccountId
integer(int64)
true
none
经销商⼦账户id
symbol
string
false
none
symbol
takerAdjustment
integer(int32)
false
none
takerAdjustment
takerCommission
integer(int32)
false
none
takerCommission
BrokerFreezeLogResponse
{ 
  "amount": 0, 
  "asset": "string", 
  "brokerParentId": 0, 


---

## Page 64

sapi-v7.4.md
2024-05-08
64 / 419
  "brokerSubAccountId": 0, 
  "clientTransId": "string", 
  "operateType": "FREEZE", 
  "status": "FAILURE", 
  "time": 0, 
  "tranId": "string" 
} 
 
BrokerFreezeLogResponse
42.70. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
冻结数量
asset
string
false
none
资产名字(例如BTC)
brokerParentId
integer(int64)
false
none
broker⺟账号userId
brokerSubAccountId
integer(int64)
false
none
broker⼦账号brokerSubAccountId
clientTransId
string
false
none
第三⽅交易id，必须唯⼀
operateType
string
false
none
操作类型，冻结或解冻
status
string
false
none
状态
time
integer(int64)
false
none
操作时间
tranId
string
false
none
内部交易id
42.70.1. Enumerated Values
Property
Value
operateType
FREEZE
operateType
UNFREEZE
status
FAILURE
status
INIT
status
PROCESS
status
SUCCESS
BrokerFutureCommissionRes
{ 
  "asset": "string", 
  "income": "string", 
  "status": 0, 
  "subaccountId": "string", 
  "symbol": "string", 
  "time": 0, 
  "tradeId": 0 
} 
 
BrokerFutureCommissionRes
42.71. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
income
string
false
none
none
status
integer(int32)
false
none
none
subaccountId
string
false
none
none
symbol
string
false
none
none
time
integer(int64)
false
none
none
tradeId
integer(int64)
false
none
none


---

## Page 65

sapi-v7.4.md
2024-05-08
65 / 419
BrokerFutureTransferRes
{ 
  "clientTranId": "string", 
  "success": true, 
  "txnId": 0 
} 
 
BrokerFutureTransferRes
42.72. Properties
Name
Type
Required
Restrictions
Description
clientTranId
string
false
none
none
success
boolean
false
none
none
txnId
integer(int64)
false
none
none
BrokerQueryCommissionDeliveryFuturesResponse
{ 
  "makerAdjustment": 0, 
  "makerCommission": 0, 
  "subAccountId": 0, 
  "symbol": "string", 
  "takerAdjustment": 0, 
  "takerCommission": 0 
} 
 
BrokerQueryCommissionDeliveryFuturesResponse
42.73. Properties
Name
Type
Required
Restrictions
Description
makerAdjustment
integer(int32)
false
none
makerAdjustment
makerCommission
integer(int32)
false
none
makerCommission
subAccountId
integer(int64)
true
none
经销商⼦账户id
symbol
string
false
none
symbol
takerAdjustment
integer(int32)
false
none
takerAdjustment
takerCommission
integer(int32)
false
none
takerCommission
BrokerQueryCommissionFuturesResponse
{ 
  "makerAdjustment": 0, 
  "makerCommission": 0, 
  "subAccountId": 0, 
  "symbol": "string", 
  "takerAdjustment": 0, 
  "takerCommission": 0 
} 
 
BrokerQueryCommissionFuturesResponse
42.74. Properties
Name
Type
Required
Restrictions
Description
makerAdjustment
integer(int32)
false
none
makerAdjustment
makerCommission
integer(int32)
false
none
makerCommission
subAccountId
integer(int64)
true
none
经销商⼦账户id


---

## Page 66

sapi-v7.4.md
2024-05-08
66 / 419
Name
Type
Required
Restrictions
Description
symbol
string
false
none
symbol
takerAdjustment
integer(int32)
false
none
takerAdjustment
takerCommission
integer(int32)
false
none
takerCommission
BrokerSettlementLogResponse
{ 
  "amount": 0, 
  "asset": "string", 
  "brokerParentId": 0, 
  "brokerSubAccountId": 0, 
  "clientTransId": "string", 
  "recipientSubAccountId": 0, 
  "status": "FAILURE", 
  "time": 0, 
  "tranId": "string" 
} 
 
BrokerSettlementLogResponse
42.75. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
⽀付数量
asset
string
false
none
资产名字(例如BTC)
brokerParentId
integer(int64)
false
none
broker⺟账号userId
brokerSubAccountId
integer(int64)
false
none
⽀付⽅SubAccountId
clientTransId
string
false
none
第三⽅交易id，必须唯⼀
recipientSubAccountId
integer(int64)
false
none
接收⽅SuAccountId
status
string
false
none
状态
time
integer(int64)
false
none
操作时间
tranId
string
false
none
内部交易id
42.75.1. Enumerated Values
Property
Value
status
FAILURE
status
INIT
status
PROCESS
status
SUCCESS
BrokerSettlementResponse
{ 
  "clientTransId": "string", 
  "errorMessage": "string", 
  "status": "FAILURE", 
  "tranId": 0 
} 
 
BrokerSettlementResponse
42.76. Properties
Name
Type
Required
Restrictions
Description
clientTransId
string
false
none
三⽅的交易id，必须唯⼀
errorMessage
string
false
none
错误信息


---

## Page 67

sapi-v7.4.md
2024-05-08
67 / 419
Name
Type
Required
Restrictions
Description
status
string
false
none
状态
tranId
integer(int64)
false
none
tranId
42.76.1. Enumerated Values
Property
Value
status
FAILURE
status
INIT
status
PROCESS
status
SUCCESS
BrokerSubAccountUniversalTransferHistoryVo
{ 
  "asset": "string", 
  "clientTranId": "string", 
  "fromAccountType": "string", 
  "fromId": "string", 
  "qty": "string", 
  "status": "string", 
  "time": 0, 
  "toAccountType": "string", 
  "toId": "string", 
  "txnId": 0 
} 
 
BrokerSubAccountUniversalTransferHistoryVo
42.77. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
clientTranId
string
false
none
none
fromAccountType
string
false
none
none
fromId
string
false
none
none
qty
string
false
none
none
status
string
false
none
none
time
integer(int64)
false
none
none
toAccountType
string
false
none
none
toId
string
false
none
none
txnId
integer(int64)
false
none
none
BrokerSubAccountUniversalTransferResponse
{ 
  "clientTranId": "string", 
  "txnId": 0 
} 
 
BrokerSubAccountUniversalTransferResponse
42.78. Properties
Name
Type
Required
Restrictions
Description
clientTranId
string
false
none
三⽅交易流⽔号
txnId
integer(int64)
false
none
事务操作id


---

## Page 68

sapi-v7.4.md
2024-05-08
68 / 419
BrokerSubMarginInterestBnbBurnSwitchResp
{ 
  "interestBNBBurn": true, 
  "subAccountId": 0 
} 
 
BrokerSubMarginInterestBnbBurnSwitchResp
42.79. Properties
Name
Type
Required
Restrictions
Description
interestBNBBurn
boolean
true
none
interestBNBBurn
subAccountId
integer(int64)
true
none
经销商⼦账户id
BrokerSubUserFutureAccountResp
{ 
  "deliveryAccountResp": { 
    "assets": [ 
      { 
        "asset": "string", 
        "initialMargin": "string", 
        "maintenanceMargin": "string", 
        "marginBalance": "string", 
        "maxWithdrawAmount": "string", 
        "openOrderInitialMargin": "string", 
        "positionInitialMargin": "string", 
        "unrealizedProfit": "string", 
        "updateTime": 0, 
        "walletBalance": "string" 
      } 
    ], 
    "canDeposit": true, 
    "canTrade": true, 
    "canWithdraw": true, 
    "email": "string", 
    "feeTier": 0, 
    "updateTime": 0 
  }, 
  "futureAccountResp": { 
    "asset": "string", 
    "assets": [ 
      { 
        "asset": "string", 
        "initialMargin": "string", 
        "maintenanceMargin": "string", 
        "marginBalance": "string", 
        "maxWithdrawAmount": "string", 
        "openOrderInitialMargin": "string", 
        "positionInitialMargin": "string", 
        "unrealizedProfit": "string", 
        "updateTime": 0, 
        "walletBalance": "string" 
      } 
    ], 
    "canDeposit": true, 
    "canTrade": true, 
    "canWithdraw": true, 
    "email": "string", 
    "feeTier": 0, 
    "maxWithdrawAmount": "string", 
    "totalInitialMargin": "string", 
    "totalMaintenanceMargin": "string", 
    "totalMarginBalance": "string", 
    "totalOpenOrderInitialMargin": "string", 
    "totalPositionInitialMargin": "string", 
    "totalUnrealizedProfit": "string", 
    "totalWalletBalance": "string", 
    "updateTime": 0 
  } 
} 
 


---

## Page 69

sapi-v7.4.md
2024-05-08
69 / 419
BrokerSubUserFutureAccountResp
42.80. Properties
Name
Type
Required
Restrictions
Description
deliveryAccountResp
QueryBrokerSubAccountDeliveryAccountResp
false
none
币本位合约账户详情
futureAccountResp
QueryBrokerSubAccountFutureAccountResp
false
none
U本位合约账户详情
CancelOcoOrderResp
{ 
  "contingencyType": "string", 
  "isIsolated": true, 
  "listClientOrderId": "string", 
  "listOrderStatus": "string", 
  "listStatusType": "string", 
  "orderListId": 0, 
  "orderReports": [ 
    { 
      "clientOrderId": "string", 
      "cummulativeQuoteQty": 0, 
      "executedQty": 0, 
      "orderId": 0, 
      "orderListId": 0, 
      "origClientOrderId": "string", 
      "origQty": "string", 
      "price": "string", 
      "selfTradePreventionMode": "string", 
      "side": "string", 
      "status": "string", 
      "stopPrice": "string", 
      "symbol": "string", 
      "timeInForce": "string", 
      "type": "string" 
    } 
  ], 
  "orders": [ 
    { 
      "clientOrderId": "string", 
      "orderId": 0, 
      "symbol": "string" 
    } 
  ], 
  "symbol": "string", 
  "transactionTime": 0 
} 
 
CancelOcoOrderResp
42.81. Properties
Name
Type
Required
Restrictions
Description
contingencyType
string
false
none
none
isIsolated
boolean
false
none
none
listClientOrderId
string
false
none
none
listOrderStatus
string
false
none
none
listStatusType
string
false
none
none
orderListId
integer(int64)
false
none
none
orderReports
[OrderReports]
false
none
none
orders
[Orders]
false
none
none
symbol
string
false
none
none
transactionTime
integer(int64)
false
none
none
CancelOrderReq


---

## Page 70

sapi-v7.4.md
2024-05-08
70 / 419
{ 
  "orders": [ 
    { 
      "orderId": 0 
    } 
  ] 
} 
 
CancelOrderReq
42.82. Properties
Name
Type
Required
Restrictions
Description
orders
[Order]
false
none
none
CancelOrderResp
{ 
  "code": 0, 
  "msg": "string", 
  "orderId": 0 
} 
 
CancelOrderResp
42.83. Properties
Name
Type
Required
Restrictions
Description
code
integer(int32)
false
none
none
msg
string
false
none
none
orderId
integer(int64)
false
none
none
CancelOrderResponse
{ 
  "algoId": 0, 
  "code": 0, 
  "msg": "string", 
  "success": true 
} 
 
CancelOrderResponse
42.84. Properties
Name
Type
Required
Restrictions
Description
algoId
integer(int64)
false
none
none
code
integer(int32)
false
none
none
msg
string
false
none
none
success
boolean
false
none
none
ChangeBrokerSubUserCommissionRes
{ 
  "makerCommission": 0, 
  "marginMakerCommission": 0, 
  "marginTakerCommission": 0, 
  "subAccountId": "string", 
  "takerCommission": 0 
} 
 


---

## Page 71

sapi-v7.4.md
2024-05-08
71 / 419
ChangeBrokerSubUserCommissionRes
42.85. Properties
Name
Type
Required
Restrictions
Description
makerCommission
number
false
none
none
marginMakerCommission
number
false
none
none
marginTakerCommission
number
false
none
none
subAccountId
string
false
none
none
takerCommission
number
false
none
none
ChatCredentialResp
{ 
  "chatWssUrl": "string", 
  "listenKey": "string", 
  "listenToken": "string" 
} 
 
ChatCredentialResp
42.86. Properties
Name
Type
Required
Restrictions
Description
chatWssUrl
string
false
none
chat WSS URL
listenKey
string
false
none
wss listen key
listenToken
string
false
none
wss listen token. Authentication is required when connecting to WSS
CheckAccountTypeResponse
{ 
  "accountTypeInfoVos": [ 
    { 
      "parentUserId": "string", 
      "remark": "string", 
      "subUser": true, 
      "userId": "string", 
      "userStatusEx": {} 
    } 
  ] 
} 
 
CheckAccountTypeResponse
42.87. Properties
Name
Type
Required
Restrictions
Description
accountTypeInfoVos
[AccountTypeInfoVo]
false
none
none
CheckCollateralRepayForSapiResp
{ 
  "collateralCoin": "string", 
  "loanCoin": "string", 
  "rate": 0, 
  "repayAmount": 0 
} 
 
CheckCollateralRepayForSapiResp
42.88. Properties


---

## Page 72

sapi-v7.4.md
2024-05-08
72 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
none
loanCoin
string
false
none
none
rate
number
false
none
none
repayAmount
number
false
none
none
CheckCustodianSubResp
{ 
  "binding": true, 
  "custodianSubUser": true, 
  "remark": "string", 
  "thirdPartyName": "string", 
  "userType": "string" 
} 
 
CheckCustodianSubResp
42.89. Properties
Name
Type
Required
Restrictions
Description
binding
boolean
false
none
none
custodianSubUser
boolean
false
none
none
remark
string
false
none
none
thirdPartyName
string
false
none
三⽅机构名称(对应全部是⼩写)
userType
string
false
none
⽤户类型
ClaimRewardsResp
{ 
  "success": true 
} 
 
ClaimRewardsResp
42.90. Properties
Name
Type
Required
Restrictions
Description
success
boolean
false
none
none
ClaimedHistoryResp
{ 
  "assetRewards": "string", 
  "claimAmount": 0, 
  "claimedTime": 0, 
  "poolId": 0, 
  "poolName": "string", 
  "status": 0 
} 
 
ClaimedHistoryResp
42.91. Properties
Name
Type
Required
Restrictions
Description
assetRewards
string
false
none
none
claimAmount
number
false
none
none
claimedTime
integer(int64)
false
none
none


---

## Page 73

sapi-v7.4.md
2024-05-08
73 / 419
Name
Type
Required
Restrictions
Description
poolId
integer(int64)
false
none
none
poolName
string
false
none
none
status
integer(int32)
false
none
none
CloudOrderVo
{ 
  "clientOrderId": "string", 
  "cummulativeQuoteQty": 0, 
  "executedQty": 0, 
  "icebergQty": 0, 
  "isWorking": true, 
  "orderId": 0, 
  "orderListId": 0, 
  "origQty": 0, 
  "origQuoteOrderQty": 0, 
  "price": 0, 
  "side": "string", 
  "status": "string", 
  "stopPrice": 0, 
  "symbol": "string", 
  "time": 0, 
  "timeInForce": "string", 
  "type": "string", 
  "updateTime": 0 
} 
 
CloudOrderVo
42.92. Properties
Name
Type
Required
Restrictions
Description
clientOrderId
string
false
none
none
cummulativeQuoteQty
number
false
none
none
executedQty
number
false
none
none
icebergQty
number
false
none
none
isWorking
boolean
false
none
none
orderId
integer(int64)
false
none
none
orderListId
integer(int64)
false
none
none
origQty
number
false
none
none
origQuoteOrderQty
number
false
none
none
price
number
false
none
none
side
string
false
none
none
status
string
false
none
none
stopPrice
number
false
none
none
symbol
string
false
none
none
time
integer(int64)
false
none
none
timeInForce
string
false
none
none
type
string
false
none
none
updateTime
integer(int64)
false
none
none
CloudPartnerTransferInResp
{ 
  "status": "string" 
} 
 


---

## Page 74

sapi-v7.4.md
2024-05-08
74 / 419
CloudPartnerTransferInResp
42.93. Properties
Name
Type
Required
Restrictions
Description
status
string
true
none
划转状态
CloudPartnerTransferResp
{ 
  "failure": true, 
  "fromResponse": "string", 
  "fromStatus": "string", 
  "success": true, 
  "toResponse": "string", 
  "toStatus": "string", 
  "tranId": 0 
} 
 
CloudPartnerTransferResp
42.94. Properties
Name
Type
Required
Restrictions
Description
failure
boolean
false
none
none
fromResponse
string
false
none
转出返回信息，仅供调⽤⽅参考，⽅便排查问题
fromStatus
string
false
none
转出状态
success
boolean
false
none
none
toResponse
string
false
none
转⼊返回信息，仅供调⽤⽅参考，⽅便排查问题
toStatus
string
false
none
转⼊状态
tranId
integer(int64)
false
none
若外部传了tranId则原样返回，未传则⾃动⽣成⼀个并返回
CloudRebateVo
{ 
  "asset": "string", 
  "delta": 0, 
  "status": 0, 
  "tranId": 0 
} 
 
CloudRebateVo
42.95. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
delta
number
false
none
none
status
integer(int32)
false
none
none
tranId
integer(int64)
false
none
none
CloudTradeVo
{ 
  "commission": 0, 
  "commissionAsset": "string", 
  "id": 0, 
  "isBestMatch": true, 
  "isBuyer": true, 
  "isMaker": true, 
  "orderId": 0, 
  "orderListId": 0, 


---

## Page 75

sapi-v7.4.md
2024-05-08
75 / 419
  "price": 0, 
  "qty": 0, 
  "quoteQty": 0, 
  "symbol": "string", 
  "time": 0 
} 
 
CloudTradeVo
42.96. Properties
Name
Type
Required
Restrictions
Description
commission
number
false
none
none
commissionAsset
string
false
none
none
id
integer(int64)
false
none
none
isBestMatch
boolean
false
none
none
isBuyer
boolean
false
none
none
isMaker
boolean
false
none
none
orderId
integer(int64)
false
none
none
orderListId
integer(int64)
false
none
none
price
number
false
none
none
qty
number
false
none
none
quoteQty
number
false
none
none
symbol
string
false
none
none
time
integer(int64)
false
none
none
CloudTransferResponse
{ 
  "errorCode": "string", 
  "errorMessage": "string", 
  "response": "string", 
  "status": "string" 
} 
 
CloudTransferResponse
42.97. Properties
Name
Type
Required
Restrictions
Description
errorCode
string
false
none
none
errorMessage
string
false
none
none
response
string
false
none
撮合返回内容
status
string
false
none
none
CoinNetworkMappingResp
{ 
  "coin": "string", 
  "depositAllEnable": true, 
  "free": 0, 
  "freeze": 0, 
  "ipoable": 0, 
  "ipoing": 0, 
  "isLegalMoney": true, 
  "locked": 0, 
  "name": "string", 
  "networkList": [ 
    { 
      "addressRegex": "string", 


---

## Page 76

sapi-v7.4.md
2024-05-08
76 / 419
      "addressRule": "string", 
      "busy": true, 
      "coin": "string", 
      "contractAddress": "string", 
      "contractAddressUrl": "string", 
      "country": "string", 
      "depositDesc": "string", 
      "depositDust": 0, 
      "depositEnable": true, 
      "entityTag": "string", 
      "estimatedArrivalTime": 0, 
      "isDefault": true, 
      "memoRegex": "string", 
      "minConfirm": 0, 
      "name": "string", 
      "network": "string", 
      "resetAddressStatus": true, 
      "sameAddress": true, 
      "specialTips": "string", 
      "specialWithdrawTips": "string", 
      "unLockConfirm": 0, 
      "withdrawDesc": "string", 
      "withdrawEnable": true, 
      "withdrawFee": 0, 
      "withdrawIntegerMultiple": 0, 
      "withdrawMax": 0, 
      "withdrawMin": 0 
    } 
  ], 
  "storage": 0, 
  "trading": true, 
  "withdrawAllEnable": true, 
  "withdrawing": 0 
} 
 
CoinNetworkMappingResp
42.98. Properties
Name
Type
Required
Restrictions
Description
coin
string
false
none
none
depositAllEnable
boolean
false
none
none
free
number
false
none
none
freeze
number
false
none
none
ipoable
number
false
none
none
ipoing
number
false
none
none
isLegalMoney
boolean
false
none
none
locked
number
false
none
none
name
string
false
none
none
networkList
[NetworkCoinMappingResp]
false
none
none
storage
number
false
none
none
trading
boolean
false
none
none
withdrawAllEnable
boolean
false
none
none
withdrawing
number
false
none
none
Collateral
{ 
  "collateralCoin": "string", 
  "currentCollateralRate": 0, 
  "interest": 0, 
  "interestFreeLimitUsed": 0, 
  "loanAmount": 0, 
  "loanCoin": "string", 
  "locked": 0, 
  "principalForInterest": 0 


---

## Page 77

sapi-v7.4.md
2024-05-08
77 / 419
} 
 
Collateral
42.99. Properties
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
抵押币种
currentCollateralRate
number
false
none
质押率
interest
number
false
none
利息
interestFreeLimitUsed
number
false
none
已⽤免息额度
loanAmount
number
false
none
放贷⾦额
loanCoin
string
false
none
借贷币种
locked
number
false
none
抵押⾦额
principalForInterest
number
false
none
计算利息的本⾦数量
CollateralAssetsDataForSapiResp
{ 
  "collateralCoin": "string", 
  "initialLTV": 0, 
  "liquidationLTV": 0, 
  "marginCallLTV": 0, 
  "maxLimit": 0, 
  "vipLevel": 0 
} 
 
CollateralAssetsDataForSapiResp
42.100. Properties
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
none
initialLTV
number
false
none
none
liquidationLTV
number
false
none
none
marginCallLTV
number
false
none
none
maxLimit
number
false
none
none
vipLevel
integer(int32)
false
none
none
CollateralRateResp
{ 
  "asset": "string", 
  "collateralRate": "string" 
} 
 
CollateralRateResp
42.101. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
collateralRate
string
false
none
none
CollateralRecordResp


---

## Page 78

sapi-v7.4.md
2024-05-08
78 / 419
{ 
  "amount": 0, 
  "asset": "string", 
  "createTime": 0, 
  "productName": "string", 
  "status": "string", 
  "type": "string" 
} 
 
CollateralRecordResp
42.102. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
createTime
integer(int64)
false
none
none
productName
string
false
none
none
status
string
false
none
none
type
string
false
none
none
ConfirmFundInfoParam
{ 
  "address": "string", 
  "addressTag": "string", 
  "depositId": 0 
} 
 
ConfirmFundInfoParam
42.103. Properties
Name
Type
Required
Restrictions
Description
address
string
true
none
确认地址
addressTag
string
false
none
确认地址tag, optional
depositId
integer(int64)
true
none
充值记录id
ConfirmOrderPaidReq
{ 
  "authType": "FIDO2", 
  "code": "string", 
  "confirmPaidType": "string", 
  "emailVerifyCode": "string", 
  "googleVerifyCode": "string", 
  "mobileVerifyCode": "string", 
  "orderNumber": "string", 
  "payId": 0, 
  "yubikeyVerifyCode": "string" 
} 
 
ConfirmOrderPaidReq
42.104. Properties
Name
Type
Required
Restrictions
Description
authType
string
false
none
Authenticate code type: GOOGLE
code
string
false
none
Authenticate Code
confirmPaidType
string
false
none
Type of payment confirmation (quick/normal)


---

## Page 79

sapi-v7.4.md
2024-05-08
79 / 419
Name
Type
Required
Restrictions
Description
emailVerifyCode
string
false
none
Email verification code
googleVerifyCode
string
false
none
Google verification code
mobileVerifyCode
string
false
none
Mobile verification code
orderNumber
string
false
none
Order number
payId
integer(int64)
false
none
User payment method id
yubikeyVerifyCode
string
false
none
Yubikey verification code
42.104.1. Enumerated Values
Property
Value
authType
FIDO2
authType
FUND_PWD
authType
GOOGLE
authType
SMS
ConfirmOrderReq
{ 
  "orders": [ 
    { 
      "orderId": 0 
    } 
  ] 
} 
 
ConfirmOrderReq
42.105. Properties
Name
Type
Required
Restrictions
Description
orders
[Order]
false
none
none
ConfirmOrderResp
{ 
  "clientOrderId": "string", 
  "code": 0, 
  "msg": "string", 
  "orderId": 0 
} 
 
ConfirmOrderResp
42.106. Properties
Name
Type
Required
Restrictions
Description
clientOrderId
string
false
none
none
code
integer(int32)
false
none
none
msg
string
false
none
none
orderId
integer(int64)
false
none
none
ConvertTradeHistoryResp
{ 
  "list": [ 
    { 
      "baseAmount": 0, 
      "baseAsset": "string", 


---

## Page 80

sapi-v7.4.md
2024-05-08
80 / 419
      "createTime": 0, 
      "expiredTimestamp": 0, 
      "expiredType": "string", 
      "limitPrice": 0, 
      "orderId": 0, 
      "orderStatus": "string", 
      "quoteAmount": 0, 
      "quoteAsset": "string", 
      "quoteId": "string", 
      "side": "string", 
      "walletType": "string" 
    } 
  ] 
} 
 
ConvertTradeHistoryResp
42.107. Properties
Name
Type
Required
Restrictions
Description
list
[OtcSapiLimitOrderResp]
false
none
trade orders
ConvertTransferPageResp
{ 
  "accountType": "string", 
  "deductedAmount": 0, 
  "deductedAsset": "string", 
  "status": "string", 
  "targetAmount": 0, 
  "targetAsset": "string", 
  "time": "2019-08-24T14:15:22Z", 
  "tranId": 0, 
  "type": 0 
} 
 
ConvertTransferPageResp
42.108. Properties
Name
Type
Required
Restrictions
Description
accountType
string
false
none
账户类型: MAIN-主账户, CARD-资⾦账户
deductedAmount
number
false
none
扣除数量
deductedAsset
string
false
none
扣除币种
status
string
false
none
状态:P-处理中, S-成功,F失败
targetAmount
number
false
none
⽬标币种数量
targetAsset
string
false
none
⽬标币种
time
string(date-time)
false
none
转换时间
tranId
integer(int64)
false
none
流⽔号
type
integer(int32)
false
none
交易类型
ConvertTransferResp
{ 
  "response": "string", 
  "status": "string", 
  "tranId": 0 
} 
 
ConvertTransferResp
42.109. Properties


---

## Page 81

sapi-v7.4.md
2024-05-08
81 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
response
string
false
none
status如果不为S, 撮合返回的response，仅供调⽤⽅参考，⽅便排查问题
status
string
false
none
convert transfer状态
tranId
integer(int64)
false
none
若外部传了tranId则原样返回，未传则⾃动⽣成⼀个并返回
CreateAccountResp
{ 
  "success": true, 
  "symbol": "string" 
} 
 
CreateAccountResp
42.110. Properties
Name
Type
Required
Restrictions
Description
success
boolean
false
none
none
symbol
string
false
none
none
CreateApiAgentAliasByAgentCodeReq
{ 
  "apiAgentCode": "string", 
  "customerId": "string" 
} 
 
CreateApiAgentAliasByAgentCodeReq
42.111. Properties
Name
Type
Required
Restrictions
Description
apiAgentCode
string
true
none
apiAgentCode
customerId
string
false
none
三⽅备注id
CreateApiAgentAliasRes
{ 
  "customerId": "string", 
  "email": "string" 
} 
 
CreateApiAgentAliasRes
42.112. Properties
Name
Type
Required
Restrictions
Description
customerId
string
false
none
customerId
email
string
false
none
email
CreateBrokerSubUserApiRes
{ 
  "apiKey": "string", 
  "canTrade": true, 
  "futuresTrade": true, 
  "marginTrade": true, 
  "secretKey": "string", 
  "subaccountId": "string" 


---

## Page 82

sapi-v7.4.md
2024-05-08
82 / 419
} 
 
CreateBrokerSubUserApiRes
42.113. Properties
Name
Type
Required
Restrictions
Description
apiKey
string
false
none
none
canTrade
boolean
false
none
none
futuresTrade
boolean
false
none
none
marginTrade
boolean
false
none
none
secretKey
string
false
none
none
subaccountId
string
false
none
none
CreateBrokerSubUserResp
{ 
  "email": "string", 
  "subaccountId": "string", 
  "tag": "string" 
} 
 
CreateBrokerSubUserResp
42.114. Properties
Name
Type
Required
Restrictions
Description
email
string
false
none
email
subaccountId
string
false
none
broke⼦账号Id
tag
string
false
none
tag
CreateBrokerageBrokeredAccountResp
{ 
  "email": "string", 
  "subAccountId": 0, 
  "tag": "string" 
} 
 
CreateBrokerageBrokeredAccountResp
42.115. Properties
Name
Type
Required
Restrictions
Description
email
string
false
none
none
subAccountId
integer(int64)
false
none
none
tag
string
false
none
none
CreateBrokerageServicingAccountResponse
{ 
  "brokerageId": "string", 
  "servicingAccountId": "string", 
  "tag": "string" 
} 
 
CreateBrokerageServicingAccountResponse


---

## Page 83

sapi-v7.4.md
2024-05-08
83 / 419
42.116. Properties
Name
Type
Required
Restrictions
Description
brokerageId
string
false
none
none
servicingAccountId
string
false
none
none
tag
string
false
none
none
CreateFuturesForBrokerSubUserResp
{ 
  "enableFutures": true, 
  "subaccountId": "string", 
  "updateTime": 0 
} 
 
CreateFuturesForBrokerSubUserResp
42.117. Properties
Name
Type
Required
Restrictions
Description
enableFutures
boolean
false
none
是否enable futures
subaccountId
string
false
none
broke⼦账号Id
updateTime
integer(int64)
false
none
更新时间
CreateIfsApplyResp
{ 
  "direction": "string", 
  "id": 0, 
  "status": "string" 
} 
 
CreateIfsApplyResp
42.118. Properties
Name
Type
Required
Restrictions
Description
direction
string
false
none
借/还
id
integer(int64)
false
none
none
status
string
false
none
审批状态
CreateMarginForBrokerSubUserResp
{ 
  "enableMargin": true, 
  "subaccountId": "string", 
  "updateTime": 0 
} 
 
CreateMarginForBrokerSubUserResp
42.119. Properties
Name
Type
Required
Restrictions
Description
enableMargin
boolean
false
none
是否enable margin
subaccountId
string
false
none
broke⼦账号Id
updateTime
integer(int64)
false
none
更新时间
CreateOrderReq


---

## Page 84

sapi-v7.4.md
2024-05-08
84 / 419
{ 
  "orders": [ 
    { 
      "orderId": 0 
    } 
  ] 
} 
 
CreateOrderReq
42.120. Properties
Name
Type
Required
Restrictions
Description
orders
[Order]
false
none
none
CreateOrderResp
{ 
  "clientOrderId": "string", 
  "code": 0, 
  "msg": "string", 
  "orderId": 0 
} 
 
CreateOrderResp
42.121. Properties
Name
Type
Required
Restrictions
Description
clientOrderId
string
false
none
none
code
integer(int32)
false
none
none
msg
string
false
none
none
orderId
integer(int64)
false
none
none
CreateSubAccountFundAutoApiKeyResp
{ 
  "apiKey": "string", 
  "secretKey": "string" 
} 
 
CreateSubAccountFundAutoApiKeyResp
42.122. Properties
Name
Type
Required
Restrictions
Description
apiKey
string
false
none
apiKey
secretKey
string
false
none
secretKey
CreateVirtualSubAccountResp
{ 
  "email": "string" 
} 
 
CreateVirtualSubAccountResp
42.123. Properties
Name
Type
Required
Restrictions
Description


---

## Page 85

sapi-v7.4.md
2024-05-08
85 / 419
Name
Type
Required
Restrictions
Description
email
string
false
read-only
账号
CustodyTransferHistoryResp
{ 
  "amount": 0, 
  "asset": "string", 
  "clientTranId": "string", 
  "time": "2019-08-24T14:15:22Z", 
  "transferType": "string" 
} 
 
CustodyTransferHistoryResp
42.124. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
交易⾦额
asset
string
false
none
币种
clientTranId
string
false
none
外部唯⼀流⽔号
time
string(date-time)
false
none
新增时间
transferType
string
false
none
OUT:从prime wallet划出,IN:划⼊prime wallet
CustodyTransferResp
{ 
  "errorCode": "string", 
  "errorMessage": "string", 
  "status": "string", 
  "tranId": 0 
} 
 
CustodyTransferResp
42.125. Properties
Name
Type
Required
Restrictions
Description
errorCode
string
false
none
失败错误码
errorMessage
string
false
none
失败错误原因
status
string
false
none
划转状态:S->成功 F->失败 P->处理中
tranId
integer(int64)
false
none
内部交易流⽔
CustodyUserAssetResp
{ 
  "asset": "string", 
  "free": 0, 
  "freeze": 0, 
  "locked": 0, 
  "withdrawing": 0 
} 
 
CustodyUserAssetResp
42.126. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none


---

## Page 86

sapi-v7.4.md
2024-05-08
86 / 419
Name
Type
Required
Restrictions
Description
free
number
false
none
none
freeze
number
false
none
none
locked
number
false
none
none
withdrawing
number
false
none
none
CustomValidateRequest
{ 
  "address": "string", 
  "coin": "string", 
  "memo": "string", 
  "network": "string" 
} 
 
CustomValidateRequest
42.127. Properties
Name
Type
Required
Restrictions
Description
address
string
false
none
none
coin
string
false
none
none
memo
string
false
none
none
network
string
false
none
none
CustomValidateResponse
{ 
  "message": "string", 
  "result": true, 
  "subCode": "string" 
} 
 
CustomValidateResponse
42.128. Properties
Name
Type
Required
Restrictions
Description
message
string
false
none
⼀级错误码(原错误信息)
result
boolean
false
none
校验结果
subCode
string
false
none
⼆级错误码
DailyProductResp
{ 
  "asset": "string", 
  "avgAnnualInterestRate": 0, 
  "canPurchase": true, 
  "canRedeem": true, 
  "featured": true, 
  "latestAnnualInterestRate": 0, 
  "minPurchaseAmount": 0, 
  "productId": "string", 
  "purchasedAmount": 0, 
  "status": "CREATED", 
  "tierAnnualInterestRate": { 
    "property1": "string", 
    "property2": "string" 
  }, 
  "upLimit": 0, 
  "upLimitPerUser": 0 
} 
 


---

## Page 87

sapi-v7.4.md
2024-05-08
87 / 419
DailyProductResp
42.129. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
币种
avgAnnualInterestRate
number
false
none
7⽇平均年化利率
canPurchase
boolean
false
none
申购状态: 开启、关闭
canRedeem
boolean
false
none
赎回状态: 开启、关闭
featured
boolean
false
none
是否推荐
latestAnnualInterestRate
number
false
none
市场化利率
minPurchaseAmount
number
false
none
最⼩申购额度
productId
string
false
none
产品Id
purchasedAmount
number
false
none
已经购买的⾦额
status
string
false
none
项⽬状态: 0新建、10预热中、20申购中、30结束
tierAnnualInterestRate
object
false
none
阶梯利率列表
» additionalProperties
string
false
none
none
upLimit
number
false
none
单⽇购买上限
upLimitPerUser
number
false
none
单⽇单⼈购买上限
42.129.1. Enumerated Values
Property
Value
status
CREATED
status
END
status
PREHEATING
status
PURCHASING
DailyRedemptionResultResp
{ 
  "clientRedeemId": "string" 
} 
 
DailyRedemptionResultResp
42.130. Properties
Name
Type
Required
Restrictions
Description
clientRedeemId
string
false
none
none
DailyTokenPositionResp
{ 
  "annualInterestRate": 0, 
  "asset": "string", 
  "avgAnnualInterestRate": 0, 
  "canRedeem": true, 
  "collateralAmount": 0, 
  "dailyInterestRate": 0, 
  "freeAmount": 0, 
  "freezeAmount": 0, 
  "lockedAmount": 0, 
  "productId": "string", 
  "productName": "string", 
  "redeemingAmount": 0, 
  "tierAnnualInterestRate": { 
    "property1": "string", 


---

## Page 88

sapi-v7.4.md
2024-05-08
88 / 419
    "property2": "string" 
  }, 
  "todayPurchasedAmount": 0, 
  "totalAmount": 0, 
  "totalBonusRewards": 0, 
  "totalInterest": 0, 
  "totalMarketRewards": 0 
} 
 
DailyTokenPositionResp
42.131. Properties
Name
Type
Required
Restrictions
Description
annualInterestRate
number
false
none
年利率
asset
string
false
none
币种
avgAnnualInterestRate
number
false
none
7⽇平均年化利率
canRedeem
boolean
false
none
是否可以赎回
collateralAmount
number
false
none
Collateral amount
dailyInterestRate
number
false
none
⽇利率
freeAmount
number
false
none
流通⾦额
freezeAmount
number
false
none
冻结⾦额
lockedAmount
number
false
none
锁仓⾦额
productId
string
false
none
产品ID
productName
string
false
none
产品名称
redeemingAmount
number
false
none
赎回中的⾦额
tierAnnualInterestRate
object
false
none
阶梯利率列表
» additionalProperties
string
false
none
none
todayPurchasedAmount
number
false
none
今⽇申购数量
totalAmount
number
false
none
总数量
totalBonusRewards
number
false
none
Total bonus reward
totalInterest
number
false
none
累计收益
totalMarketRewards
number
false
none
Total market reward
DailyUserRedemptionQuotaResp
{ 
  "asset": "string", 
  "dailyQuota": 0, 
  "leftQuota": 0, 
  "minRedemptionAmount": 0 
} 
 
DailyUserRedemptionQuotaResp
42.132. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
dailyQuota
number
false
none
none
leftQuota
number
false
none
none
minRedemptionAmount
number
false
none
none
DcPositionOrderSapiDto


---

## Page 89

sapi-v7.4.md
2024-05-08
89 / 419
{ 
  "list": [ 
    { 
      "apr": 0, 
      "asset": "string", 
      "canPurchase": true, 
      "duration": 0, 
      "extraRewardAPR": 0, 
      "extraRewardAsset": "string", 
      "isSoldOut": true, 
      "renewable": true, 
      "rewardAsset": "string", 
      "status": "string", 
      "subscriptionStartTime": 0 
    } 
  ], 
  "total": 0 
} 
 
DcPositionOrderSapiDto
42.133. Properties
Name
Type
Required
Restrictions
Description
list
[Detail]
false
none
project list
total
integer(int64)
false
none
total
DcPositionSummarySapiDto
{ 
  "totalAmountInBTC": 0, 
  "totalAmountInUSDT": 0 
} 
 
DcPositionSummarySapiDto
42.134. Properties
Name
Type
Required
Restrictions
Description
totalAmountInBTC
number
false
none
none
totalAmountInUSDT
number
false
none
none
DcPositionUpdateAutoCompoundPlanResultDto
{ 
  "autoCompoundPlan": "ADVANCE", 
  "positionId": 0, 
  "projectId": "string" 
} 
 
DcPositionUpdateAutoCompoundPlanResultDto
42.135. Properties
Name
Type
Required
Restrictions
Description
autoCompoundPlan
string
false
none
auto compound plan
positionId
integer(int64)
false
none
position id
projectId
string
false
none
project id
42.135.1. Enumerated Values
Property
Value
autoCompoundPlan
ADVANCE


---

## Page 90

sapi-v7.4.md
2024-05-08
90 / 419
Property
Value
autoCompoundPlan
NONE
autoCompoundPlan
STANDARD
DcProjectDisplaySapiDto
{ 
  "list": [ 
    { 
      "apr": 0, 
      "autoCompoundPlanList": [ 
        "string" 
      ], 
      "canPurchase": true, 
      "createTimestamp": 0, 
      "duration": 0, 
      "exercisedCoin": "string", 
      "id": "string", 
      "investCoin": "string", 
      "isAutoCompoundEnable": true, 
      "maxAmount": 0, 
      "minAmount": 0, 
      "optionType": "string", 
      "orderId": 0, 
      "purchaseDecimal": 0, 
      "purchaseEndTime": 0, 
      "settleDate": 0, 
      "strikePrice": 0 
    } 
  ], 
  "total": 0 
} 
 
DcProjectDisplaySapiDto
42.136. Properties
Name
Type
Required
Restrictions
Description
list
[Detail0]
false
none
project list
total
integer(int64)
false
none
total
DcPurchaseProjectSapiResultDto
{ 
  "apr": 0, 
  "autoCompoundPlan": "string", 
  "duration": 0, 
  "exercisedCoin": "string", 
  "investCoin": "string", 
  "optionType": "string", 
  "orderId": 0, 
  "positionId": 0, 
  "purchaseStatus": "string", 
  "purchaseTime": 0, 
  "settleDate": 0, 
  "strikePrice": 0, 
  "subscriptionAmount": 0 
} 
 
DcPurchaseProjectSapiResultDto
42.137. Properties
Name
Type
Required
Restrictions
Description
apr
number
false
none
none
autoCompoundPlan
string
false
none
auto compound plan
duration
integer(int32)
false
none
none


---

## Page 91

sapi-v7.4.md
2024-05-08
91 / 419
Name
Type
Required
Restrictions
Description
exercisedCoin
string
false
none
none
investCoin
string
false
none
none
optionType
string
false
none
none
orderId
integer(int64)
false
none
none
positionId
integer(int64)
false
none
subscription id
purchaseStatus
string
false
none
none
purchaseTime
integer(int64)
false
none
none
settleDate
integer(int64)
false
none
project settle date
strikePrice
number
false
none
strike price / linked price
subscriptionAmount
number
false
none
none
DcSettlementDetailSapiResp
{ 
  "code": "string", 
  "detailList": [ 
    { 
      "bnPayingAmount": 0, 
      "bnPayingToken": "string", 
      "bnReceivingAmount": 0, 
      "bnReceivingToken": "string", 
      "createTime": 0, 
      "depositAmount": 0, 
      "depositAsset": "string", 
      "fixingTime": 0, 
      "isExercised": true, 
      "positionId": 0, 
      "premiumAmount": 0, 
      "underlyingPair": [ 
        "string" 
      ] 
    } 
  ], 
  "fixingTime": 0, 
  "message": "string", 
  "totalCount": 0 
} 
 
DcSettlementDetailSapiResp
42.138. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
detailList
[DcSubscriptionSettlementDetailSapiResp]
false
none
none
fixingTime
integer(int64)
false
none
none
message
string
false
none
none
totalCount
integer(int32)
false
none
none
DcSettlementPremiumReconReq
{ 
  "fixingTime": 0, 
  "reconData": [ 
    { 
      "altToken": "string", 
      "depositToken": "string", 
      "sumPremium": 0, 
      "sumQty": 0, 
      "underlying": "string" 
    } 
  ] 


---

## Page 92

sapi-v7.4.md
2024-05-08
92 / 419
} 
 
DcSettlementPremiumReconReq
42.139. Properties
Name
Type
Required
Restrictions
Description
fixingTime
integer(int64)
false
none
none
reconData
[DcSettlementPremiumSummaryArg]
false
none
none
DcSettlementPremiumReconSapiResp
{ 
  "code": "string", 
  "fixingTime": 0, 
  "message": "string" 
} 
 
DcSettlementPremiumReconSapiResp
42.140. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
fixingTime
integer(int64)
false
none
none
message
string
false
none
none
DcSettlementPremiumSummaryArg
{ 
  "altToken": "string", 
  "depositToken": "string", 
  "sumPremium": 0, 
  "sumQty": 0, 
  "underlying": "string" 
} 
 
DcSettlementPremiumSummaryArg
42.141. Properties
Name
Type
Required
Restrictions
Description
altToken
string
false
none
none
depositToken
string
false
none
none
sumPremium
number
false
none
none
sumQty
number
false
none
none
underlying
string
false
none
none
DcSettlementReconConfirmArg
{ 
  "fixingTime": 0, 
  "isExercised": true 
} 
 
DcSettlementReconConfirmArg
42.142. Properties


---

## Page 93

sapi-v7.4.md
2024-05-08
93 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
fixingTime
integer(int64)
false
none
none
isExercised
boolean
false
none
none
DcSettlementReconSapiResp
{ 
  "code": "string", 
  "fixingTime": 0, 
  "message": "string" 
} 
 
DcSettlementReconSapiResp
42.143. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
fixingTime
integer(int64)
false
none
none
message
string
false
none
none
DcSettlementSummaryDetailSapiResp
{ 
  "bnPayingAmount": 0, 
  "bnReceivingAmount": 0, 
  "coin": "string", 
  "fixingTime": 0, 
  "totalNettingAmount": 0 
} 
 
DcSettlementSummaryDetailSapiResp
42.144. Properties
Name
Type
Required
Restrictions
Description
bnPayingAmount
number
false
none
none
bnReceivingAmount
number
false
none
none
coin
string
false
none
none
fixingTime
integer(int64)
false
none
none
totalNettingAmount
number
false
none
none
DcSettlementSummarySapiResp
{ 
  "code": "string", 
  "fixingTime": 0, 
  "message": "string", 
  "summaryList": [ 
    { 
      "bnPayingAmount": 0, 
      "bnReceivingAmount": 0, 
      "coin": "string", 
      "fixingTime": 0, 
      "totalNettingAmount": 0 
    } 
  ] 
} 
 
DcSettlementSummarySapiResp


---

## Page 94

sapi-v7.4.md
2024-05-08
94 / 419
42.145. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
fixingTime
integer(int64)
false
none
none
message
string
false
none
none
summaryList
[DcSettlementSummaryDetailSapiResp]
false
none
none
DcSubscriptionSettlementDetailSapiResp
{ 
  "bnPayingAmount": 0, 
  "bnPayingToken": "string", 
  "bnReceivingAmount": 0, 
  "bnReceivingToken": "string", 
  "createTime": 0, 
  "depositAmount": 0, 
  "depositAsset": "string", 
  "fixingTime": 0, 
  "isExercised": true, 
  "positionId": 0, 
  "premiumAmount": 0, 
  "underlyingPair": [ 
    "string" 
  ] 
} 
 
DcSubscriptionSettlementDetailSapiResp
42.146. Properties
Name
Type
Required
Restrictions
Description
bnPayingAmount
number
false
none
none
bnPayingToken
string
false
none
none
bnReceivingAmount
number
false
none
none
bnReceivingToken
string
false
none
none
createTime
integer(int64)
false
none
none
depositAmount
number
false
none
none
depositAsset
string
false
none
none
fixingTime
integer(int64)
false
none
none
isExercised
boolean
false
none
none
positionId
integer(int64)
false
none
none
premiumAmount
number
false
none
none
underlyingPair
[string]
false
none
none
DefiFlexibleAccount
{ 
  "lastDayProfitInBTC": 0, 
  "lastDayProfitInUSDT": 0, 
  "totalAmountInBTC": 0, 
  "totalAmountInUSDT": 0 
} 
 
DefiFlexibleAccount
42.147. Properties
Name
Type
Required
Restrictions
Description
lastDayProfitInBTC
number
false
none
none


---

## Page 95

sapi-v7.4.md
2024-05-08
95 / 419
Name
Type
Required
Restrictions
Description
lastDayProfitInUSDT
number
false
none
none
totalAmountInBTC
number
false
none
none
totalAmountInUSDT
number
false
none
none
DefiLockedAccount
{ 
  "lastDayProfitInBTC": 0, 
  "lastDayProfitInUSDT": 0, 
  "totalAmountInBTC": 0, 
  "totalAmountInUSDT": 0 
} 
 
DefiLockedAccount
42.148. Properties
Name
Type
Required
Restrictions
Description
lastDayProfitInBTC
number
false
none
none
lastDayProfitInUSDT
number
false
none
none
totalAmountInBTC
number
false
none
none
totalAmountInUSDT
number
false
none
none
DeleteSubAccountFundAutoApiKeyResp
{} 
 
DeleteSubAccountFundAutoApiKeyResp
42.149. Properties
None
DelistScheduleResp
{ 
  "delistTime": 0, 
  "symbols": [ 
    "string" 
  ] 
} 
 
DelistScheduleResp
42.150. Properties
Name
Type
Required
Restrictions
Description
delistTime
integer(int64)
false
none
none
symbols
[string]
false
none
none
DeliveryAccountSummaryInfoVoSapiVersion
{ 
  "asset": "string", 
  "email": "string", 
  "totalMarginBalance": "string", 
  "totalUnrealizedProfit": "string", 
  "totalWalletBalance": "string" 
} 
 


---

## Page 96

sapi-v7.4.md
2024-05-08
96 / 419
DeliveryAccountSummaryInfoVoSapiVersion
42.151. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
email
string
false
none
none
totalMarginBalance
string
false
none
none
totalUnrealizedProfit
string
false
none
none
totalWalletBalance
string
false
none
none
DeliveryAssetRiskInfoVo
{ 
  "asset": "string", 
  "initialMargin": "string", 
  "maintenanceMargin": "string", 
  "marginBalance": "string", 
  "maxWithdrawAmount": "string", 
  "openOrderInitialMargin": "string", 
  "positionInitialMargin": "string", 
  "unrealizedProfit": "string", 
  "updateTime": 0, 
  "walletBalance": "string" 
} 
 
DeliveryAssetRiskInfoVo
42.152. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
资产类型（币种）
initialMargin
string
false
none
起始保证⾦
maintenanceMargin
string
false
none
维持保证⾦
marginBalance
string
false
none
保证⾦余额
maxWithdrawAmount
string
false
none
最⼤提现
openOrderInitialMargin
string
false
none
none
positionInitialMargin
string
false
none
none
unrealizedProfit
string
false
none
持仓未实现盈亏
updateTime
integer(int64)
false
none
最近操作时间
walletBalance
string
false
none
钱包余额
DeliveryPositionRiskVO
{ 
  "entryPrice": "string", 
  "isAutoAddMargin": "string", 
  "isolated": "string", 
  "isolatedMargin": "string", 
  "isolatedWallet": "string", 
  "leverage": "string", 
  "markPrice": "string", 
  "positionAmount": "string", 
  "positionSide": "string", 
  "symbol": "string", 
  "unrealizedProfit": "string" 
} 
 
DeliveryPositionRiskVO


---

## Page 97

sapi-v7.4.md
2024-05-08
97 / 419
42.153. Properties
Name
Type
Required
Restrictions
Description
entryPrice
string
false
none
none
isAutoAddMargin
string
false
none
none
isolated
string
false
none
none
isolatedMargin
string
false
none
none
isolatedWallet
string
false
none
none
leverage
string
false
none
none
markPrice
string
false
none
none
positionAmount
string
false
none
none
positionSide
string
false
none
none
symbol
string
false
none
none
unrealizedProfit
string
false
none
none
DepositAddressListRecResp
{ 
  "address": "string", 
  "addressCode": "string", 
  "addressTag": "string", 
  "createTime": "2019-08-24T14:15:22Z", 
  "id": 0, 
  "networkSet": [ 
    "string" 
  ], 
  "status": 0, 
  "updateTime": "2019-08-24T14:15:22Z", 
  "userId": 0 
} 
 
DepositAddressListRecResp
42.154. Properties
Name
Type
Required
Restrictions
Description
address
string
false
none
none
addressCode
string
false
none
none
addressTag
string
false
none
none
createTime
string(date-time)
false
none
none
id
integer(int64)
false
none
none
networkSet
[string]
false
none
none
status
integer(int32)
false
none
none
updateTime
string(date-time)
false
none
none
userId
integer(int64)
false
none
none
DepositAppealConfirmRequest
{ 
  "expectedAmount": 0, 
  "requestId": "string", 
  "targetAddress": "string", 
  "targetAddressTag": "string" 
} 
 
DepositAppealConfirmRequest
42.155. Properties


---

## Page 98

sapi-v7.4.md
2024-05-08
98 / 419
Name
Type
Required
Restrictions
Description
expectedAmount
number
false
none
期望上账或退回的⾦额,optional
requestId
string
false
none
找回申请单id
targetAddress
string
false
none
上账或退回的地址,optional
targetAddressTag
string
false
none
上账或退回的地址标签,optional
DepositAppealMaterialBindRequest
{ 
  "materialKey": "string", 
  "materialName": "string", 
  "refundAddress": "string", 
  "refundAddressTag": "string", 
  "requestId": "string", 
  "requestType": 0 
} 
 
DepositAppealMaterialBindRequest
42.156. Properties
Name
Type
Required
Restrictions
Description
materialKey
string
false
none
资料在s3中的路径
materialName
string
false
none
⽂件原名
refundAddress
string
false
none
更改退款地址,optional
refundAddressTag
string
false
none
更改退款地址的标签,optional
requestId
string
false
none
要绑定的充值未到账单⼦的requestId
requestType
integer(int32)
false
none
参数: 1=标签币找回, 2=充值未到账找回
DepositAppealMaterialPrepareResp
{ 
  "materialKey": "string", 
  "url": "string" 
} 
 
DepositAppealMaterialPrepareResp
42.157. Properties
Name
Type
Required
Restrictions
Description
materialKey
string
false
none
资料在s3中的路径
url
string
false
none
上传到的URL,或播放⽤的URL,会有超时时间
DepositAppealPrecheckRequest
{ 
  "amount": 0, 
  "coin": "string", 
  "depositId": 0, 
  "network": "string", 
  "toAddress": "string", 
  "txId": "string" 
} 
 
DepositAppealPrecheckRequest
42.158. Properties


---

## Page 99

sapi-v7.4.md
2024-05-08
99 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
amount
number
false
none
申请 的 txId 币种⾦额
coin
string
false
none
申请 的 txId的币种
depositId
integer(int64)
false
none
要找回的充值记录id, optional
network
string
false
none
申请 的 txId所在⽹络
toAddress
string
false
none
申请 的 txId 转账所到地址
txId
string
false
none
申请 的txId
DepositCreditApplyReq
{ 
  "depositId": 0, 
  "subAccountId": 0, 
  "subUserId": 0, 
  "txId": "string" 
} 
 
DepositCreditApplyReq
42.159. Properties
Name
Type
Required
Restrictions
Description
depositId
integer(int64)
false
none
充值记录Id,优先使⽤
subAccountId
integer(int64)
false
none
Cloud的⼦账户ID
subUserId
integer(int64)
false
none
⺟账户的⼦账户userId
txId
string
false
none
充值txId,当depositId没指定时使⽤
DepositHisRecResp
{ 
  "address": "string", 
  "addressTag": "string", 
  "amount": 0, 
  "coin": "string", 
  "confirmTimes": "string", 
  "id": "string", 
  "insertTime": 0, 
  "network": "string", 
  "sourceAddress": "string", 
  "status": 0, 
  "transferType": 0, 
  "txId": "string", 
  "unlockConfirm": 0, 
  "walletType": 0 
} 
 
DepositHisRecResp
42.160. Properties
Name
Type
Required
Restrictions
Description
address
string
false
none
none
addressTag
string
false
none
none
amount
number
false
none
none
coin
string
false
none
none
confirmTimes
string
false
none
none
id
string
false
none
none
insertTime
integer(int64)
false
none
none
network
string
false
none
none


---

## Page 100

sapi-v7.4.md
2024-05-08
100 / 419
Name
Type
Required
Restrictions
Description
sourceAddress
string
false
none
none
status
integer(int32)
false
none
none
transferType
integer(int32)
false
none
none
txId
string
false
none
none
unlockConfirm
integer(int64)
false
none
none
walletType
integer(int32)
false
none
none
DepositInquiryDetailVo
{ 
  "address": "string", 
  "amount": 0, 
  "coin": "string", 
  "completedTime": "2019-08-24T14:15:22Z", 
  "expectedAmount": 0, 
  "feeAmount": 0, 
  "feeDeducted": true, 
  "feeFreezeStatus": 0, 
  "feeRatio": 0, 
  "feeShowed": true, 
  "feeUnit": "string", 
  "heightWarn": 0, 
  "insertTime": "2019-08-24T14:15:22Z", 
  "isCoinOnline": true, 
  "manualReviewTime": "2019-08-24T14:15:22Z", 
  "materialUploadTime": "2019-08-24T14:15:22Z", 
  "materials": [ 
    { 
      "id": 0, 
      "insertTime": "2019-08-24T14:15:22Z", 
      "materialKey": "string", 
      "name": "string", 
      "requestId": "string" 
    } 
  ], 
  "needDays": 0, 
  "network": "string", 
  "noEnoughBalance": true, 
  "platformName": "string", 
  "reason": "string", 
  "reasonKey": "string", 
  "refundAddress": "string", 
  "refundAddressTag": "string", 
  "refundAmount": 0, 
  "refundCoin": "string", 
  "remark": "string", 
  "requestId": "string", 
  "requestType": 0, 
  "selfReturnStatus": 0, 
  "sourceAddress": "string", 
  "status": 0, 
  "supplementTypes": [ 
    "string" 
  ], 
  "transactionId": "string", 
  "txId": "string", 
  "type": 0, 
  "updateTime": "2019-08-24T14:15:22Z", 
  "userId": 0, 
  "workOrder": "string" 
} 
 
DepositInquiryDetailVo
42.161. Properties
Name
Type
Required
Restrictions
Description
address
string
false
none
none
amount
number
false
none
none


---

## Page 101

sapi-v7.4.md
2024-05-08
101 / 419
Name
Type
Required
Restrictions
Description
coin
string
false
none
none
completedTime
string(date-time)
false
none
none
expectedAmount
number
false
none
none
feeAmount
number
false
none
none
feeDeducted
boolean
false
none
none
feeFreezeStatus
integer(int32)
false
none
none
feeRatio
number
false
none
none
feeShowed
boolean
false
none
none
feeUnit
string
false
none
none
heightWarn
integer(int32)
false
none
none
insertTime
string(date-time)
false
none
none
isCoinOnline
boolean
false
none
none
manualReviewTime
string(date-time)
false
none
none
materialUploadTime
string(date-time)
false
none
none
materials
[DepositNotCreditMaterialVo]
false
none
none
needDays
integer(int32)
false
none
none
network
string
false
none
none
noEnoughBalance
boolean
false
none
none
platformName
string
false
none
none
reason
string
false
none
none
reasonKey
string
false
none
none
refundAddress
string
false
none
none
refundAddressTag
string
false
none
none
refundAmount
number
false
none
none
refundCoin
string
false
none
none
remark
string
false
none
none
requestId
string
false
none
none
requestType
integer(int32)
false
none
none
selfReturnStatus
integer(int32)
false
none
none
sourceAddress
string
false
none
none
status
integer(int32)
false
none
none
supplementTypes
[string]
false
none
none
transactionId
string
false
none
none
txId
string
false
none
none
type
integer(int32)
false
none
none
updateTime
string(date-time)
false
none
none
userId
integer(int64)
false
none
none
workOrder
string
false
none
none
DepositInquiryTxIdResp
{ 
  "actualNetwork": "string", 
  "amount": 0, 
  "coin": "string", 
  "dateTime": 0, 
  "network": "string", 
  "requestId": "string", 
  "requestType": 0, 
  "result": 0, 


---

## Page 102

sapi-v7.4.md
2024-05-08
102 / 419
  "status": 0 
} 
 
DepositInquiryTxIdResp
42.162. Properties
Name
Type
Required
Restrictions
Description
actualNetwork
string
false
none
⽹络代码
amount
number
false
none
币量
coin
string
false
none
币种
dateTime
integer(int64)
false
none
相关时间
network
string
false
none
⽹络显示名称
requestId
string
false
none
关联的已提交申请单id
requestType
integer(int32)
false
none
1标签币找回, 2充值未到账找回
result
integer(int32)
false
none
0=未覆盖场景；1=txId 错误；2=已经充值记录中；3=已经在申请找回中；4=充值掉单, 5=是提现
txId
status
integer(int32)
false
none
每种result有相应status对应
DepositNotCreditMaterialVo
{ 
  "id": 0, 
  "insertTime": "2019-08-24T14:15:22Z", 
  "materialKey": "string", 
  "name": "string", 
  "requestId": "string" 
} 
 
DepositNotCreditMaterialVo
42.163. Properties
Name
Type
Required
Restrictions
Description
id
integer(int64)
false
none
none
insertTime
string(date-time)
false
none
none
materialKey
string
false
none
none
name
string
false
none
none
requestId
string
false
none
none
DepositNotCreditUserVo
{ 
  "address": "string", 
  "amount": 0, 
  "coin": "string", 
  "comment": "string", 
  "feeAmount": 0, 
  "feeDeducted": true, 
  "feeFreezeStatus": 0, 
  "feeRatio": 0, 
  "feeShowed": true, 
  "feeUnit": "string", 
  "heightWarn": 0, 
  "insertTime": "2019-08-24T14:15:22Z", 
  "isCoinOnline": true, 
  "matchedCount": 0, 
  "matchedDeposit": { 
    "amount": "string", 
    "coin": "string", 
    "id": "string", 
    "network": "string", 


---

## Page 103

sapi-v7.4.md
2024-05-08
103 / 419
    "targetAddress": "string", 
    "txId": "string" 
  }, 
  "materials": [ 
    { 
      "id": 0, 
      "insertTime": "2019-08-24T14:15:22Z", 
      "materialKey": "string", 
      "name": "string", 
      "requestId": "string" 
    } 
  ], 
  "network": "string", 
  "noEnoughBalance": true, 
  "reason": "string", 
  "refundAddress": "string", 
  "refundAddressTag": "string", 
  "refundAmount": 0, 
  "refundCoin": "string", 
  "requestId": "string", 
  "status": 0, 
  "supplementTypes": [ 
    "string" 
  ], 
  "transactionId": "string", 
  "txId": "string", 
  "type": 0, 
  "unlistedCoinReturn": true, 
  "updateTime": "2019-08-24T14:15:22Z", 
  "workOrder": "string" 
} 
 
DepositNotCreditUserVo
42.164. Properties
Name
Type
Required
Restrictions
Description
address
string
false
none
none
amount
number
false
none
none
coin
string
false
none
none
comment
string
false
none
none
feeAmount
number
false
none
none
feeDeducted
boolean
false
none
⼿续费是否已扣除
feeFreezeStatus
integer(int32)
false
none
⼿续费冻结状态: 默认0-未冻结,1-尝试冻结, 2-success, 3-failed
feeRatio
number
false
none
⼿续费⽐例
feeShowed
boolean
false
none
⼿续费是否已披露
feeUnit
string
false
none
none
heightWarn
integer(int32)
false
none
none
insertTime
string(date-time)
false
none
none
isCoinOnline
boolean
false
none
none
matchedCount
integer(int32)
false
none
none
matchedDeposit
MatchedDeposit
false
none
none
materials
[DepositNotCreditMaterialVo]
false
none
none
network
string
false
none
none
noEnoughBalance
boolean
false
none
余额是否⼩于0.001BTC
reason
string
false
none
none
refundAddress
string
false
none
none
refundAddressTag
string
false
none
none
refundAmount
number
false
none
none
refundCoin
string
false
none
none


---

## Page 104

sapi-v7.4.md
2024-05-08
104 / 419
Name
Type
Required
Restrictions
Description
requestId
string
false
none
none
status
integer(int32)
false
none
none
supplementTypes
[string]
false
none
资料补充类型, 1 补充退款地址, 2 补视频
transactionId
string
false
none
none
txId
string
false
none
none
type
integer(int32)
false
none
none
unlistedCoinReturn
boolean
false
none
none
updateTime
string(date-time)
false
none
none
workOrder
string
false
none
none
Detail
{ 
  "apr": 0, 
  "asset": "string", 
  "canPurchase": true, 
  "duration": 0, 
  "extraRewardAPR": 0, 
  "extraRewardAsset": "string", 
  "isSoldOut": true, 
  "renewable": true, 
  "rewardAsset": "string", 
  "status": "string", 
  "subscriptionStartTime": 0 
} 
 
Detail
42.165. Properties
Name
Type
Required
Restrictions
Description
apr
number
false
none
none
asset
string
false
none
none
canPurchase
boolean
false
none
none
duration
integer(int32)
false
none
none
extraRewardAPR
number
false
none
none
extraRewardAsset
string
false
none
none
isSoldOut
boolean
false
none
none
renewable
boolean
false
none
none
rewardAsset
string
false
none
none
status
string
false
none
none
subscriptionStartTime
integer(int64)
false
none
none
Detail0
{ 
  "apr": 0, 
  "autoCompoundPlanList": [ 
    "string" 
  ], 
  "canPurchase": true, 
  "createTimestamp": 0, 
  "duration": 0, 
  "exercisedCoin": "string", 
  "id": "string", 
  "investCoin": "string", 
  "isAutoCompoundEnable": true, 
  "maxAmount": 0, 
  "minAmount": 0, 


---

## Page 105

sapi-v7.4.md
2024-05-08
105 / 419
  "optionType": "string", 
  "orderId": 0, 
  "purchaseDecimal": 0, 
  "purchaseEndTime": 0, 
  "settleDate": 0, 
  "strikePrice": 0 
} 
 
Detail0
42.166. Properties
Name
Type
Required
Restrictions
Description
apr
number
false
none
apr
autoCompoundPlanList
[string]
false
none
autoCompoundPlanList
canPurchase
boolean
false
none
canPurchase
createTimestamp
integer(int64)
false
none
createTimestamp
duration
integer(int32)
false
none
duration
exercisedCoin
string
false
none
target asset
id
string
false
none
id
investCoin
string
false
none
invest asset
isAutoCompoundEnable
boolean
false
none
isAutoCompoundEnable
maxAmount
number
false
none
maxAmount
minAmount
number
false
none
minAmount
optionType
string
false
none
optionType
orderId
integer(int64)
false
none
orderId
purchaseDecimal
integer(int32)
false
none
purchaseDecimal
purchaseEndTime
integer(int64)
false
none
purchaseEndTime
settleDate
integer(int64)
false
none
settle date
strikePrice
number
false
none
strikePrice
DigitalCurrencyVo
{ 
  "asset": "string", 
  "createTime": "2019-08-24T14:15:22Z", 
  "decimalScale": 0, 
  "iconUrl": "string", 
  "isEnable": 0, 
  "isTransVisible": 0, 
  "name": "string", 
  "ranking": 0, 
  "updateTime": "2019-08-24T14:15:22Z" 
} 
 
DigitalCurrencyVo
42.167. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
数字货币简写，如： BTC, BNB
createTime
string(date-time)
false
none
创建时间
decimalScale
integer(int32)
false
none
⼩数精度数
iconUrl
string
false
none
数字货币图标链接
isEnable
integer(int32)
false
none
是否有效，1有效，0⽆效
isTransVisible
integer(int32)
false
none
交易可⻅，1可⻅，0不可⻅


---

## Page 106

sapi-v7.4.md
2024-05-08
106 / 419
Name
Type
Required
Restrictions
Description
name
string
false
none
数字货币名称
ranking
integer(int32)
false
none
排名
updateTime
string(date-time)
false
none
修改时间
DotAccount
{ 
  "totalAmountInBTC": 0, 
  "totalAmountInUSDT": 0 
} 
 
DotAccount
42.168. Properties
Name
Type
Required
Restrictions
Description
totalAmountInBTC
number
false
none
none
totalAmountInUSDT
number
false
none
none
EmptyResult
{} 
 
EmptyResult
42.169. Properties
None
EnableSubUserEOptionsResp
{ 
  "email": "string", 
  "isEOptionsEnabled": true 
} 
 
EnableSubUserEOptionsResp
42.170. Properties
Name
Type
Required
Restrictions
Description
email
string
false
none
⼦账户邮箱
isEOptionsEnabled
boolean
false
none
是否启⽤EOptions
EnableSubUserLVTResp
{ 
  "email": "string", 
  "enableBlvt": true 
} 
 
EnableSubUserLVTResp
42.171. Properties
Name
Type
Required
Restrictions
Description
email
string
false
none
none


---

## Page 107

sapi-v7.4.md
2024-05-08
107 / 419
Name
Type
Required
Restrictions
Description
enableBlvt
boolean
false
none
none
EnableUniversalTransferResp
{ 
  "apiKey": "string", 
  "canUniversalTransfer": true, 
  "subAccount": "string" 
} 
 
EnableUniversalTransferResp
42.172. Properties
Name
Type
Required
Restrictions
Description
apiKey
string
false
none
none
canUniversalTransfer
boolean
false
none
none
subAccount
string
false
none
none
EnableVanillaOptionsResp
{ 
  "apiKey": "string", 
  "canVanillaOptions": true, 
  "subAccount": "string" 
} 
 
EnableVanillaOptionsResp
42.173. Properties
Name
Type
Required
Restrictions
Description
apiKey
string
false
none
none
canVanillaOptions
boolean
false
none
none
subAccount
string
false
none
none
EstimateAsset
{ 
  "amount": 0, 
  "asset": "string" 
} 
 
EstimateAsset
42.174. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
Amount
asset
string
false
none
Asset
Eth2Account
{ 
  "cumulativeProfitInBETH": 0, 
  "lastDayProfitInBETH": 0 
} 
 


---

## Page 108

sapi-v7.4.md
2024-05-08
108 / 419
Eth2Account
42.175. Properties
Name
Type
Required
Restrictions
Description
cumulativeProfitInBETH
number
false
none
none
lastDayProfitInBETH
number
false
none
none
EthHoldingDetail
{ 
  "bethAmount": 0, 
  "wbethAmount": 0 
} 
 
EthHoldingDetail
42.176. Properties
Name
Type
Required
Restrictions
Description
bethAmount
number
false
none
none
wbethAmount
number
false
none
none
EthProfitDetail
{ 
  "amountFromBETH": 0, 
  "amountFromWBETH": 0 
} 
 
EthProfitDetail
42.177. Properties
Name
Type
Required
Restrictions
Description
amountFromBETH
number
false
none
none
amountFromWBETH
number
false
none
none
ExchangeSmallLiabilityHistoryDto
{ 
  "amount": 0, 
  "asset": "string", 
  "bizType": "string", 
  "targetAmount": 0, 
  "targetAsset": "string", 
  "timestamp": 0 
} 
 
ExchangeSmallLiabilityHistoryDto
42.178. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
bizType
string
false
none
none
targetAmount
number
false
none
none
targetAsset
string
false
none
none


---

## Page 109

sapi-v7.4.md
2024-05-08
109 / 419
Name
Type
Required
Restrictions
Description
timestamp
integer(int64)
false
none
none
ExchangeSmallLiabilityResp
{ 
  "asset": "string", 
  "interest": 0, 
  "liabilityAsset": "string", 
  "liabilityQty": 0, 
  "principal": 0 
} 
 
ExchangeSmallLiabilityResp
42.179. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
interest
number
false
none
none
liabilityAsset
string
false
none
none
liabilityQty
number
false
none
none
principal
number
false
none
none
ExecutionResultResp
{ 
  "clientOrderId": "string", 
  "orderId": 0, 
  "price": 0, 
  "qty": 0, 
  "side": "BUY", 
  "symbol": "string" 
} 
 
ExecutionResultResp
42.180. Properties
Name
Type
Required
Restrictions
Description
clientOrderId
string
false
none
none
orderId
integer(int64)
false
none
none
price
number
false
none
none
qty
number
false
none
none
side
string
false
none
none
symbol
string
false
none
none
42.180.1. Enumerated Values
Property
Value
side
BUY
side
SELL
ExpireAddressResponse
{ 
  "expiredCount": 0 
} 
 


---

## Page 110

sapi-v7.4.md
2024-05-08
110 / 419
ExpireAddressResponse
42.181. Properties
Name
Type
Required
Restrictions
Description
expiredCount
integer(int32)
false
none
none
FastWithdrawSwitchResp
{ 
  "status": true 
} 
 
FastWithdrawSwitchResp
42.182. Properties
Name
Type
Required
Restrictions
Description
status
boolean
false
none
none
FetchImageUploadUrlArg
{ 
  "imageName": "string" 
} 
 
FetchImageUploadUrlArg
42.183. Properties
Name
Type
Required
Restrictions
Description
imageName
string
false
none
image file name include postfix, expired in 5min support types: jpg,jpeg,png
FetchImageUploadUrlRet
{ 
  "imageUrl": "string", 
  "uploadUrl": "string" 
} 
 
FetchImageUploadUrlRet
42.184. Properties
Name
Type
Required
Restrictions
Description
imageUrl
string
false
none
image url
uploadUrl
string
false
none
upload image url
FiatChannelProductSelector
{ 
  "assetCode": "string", 
  "assetName": "string", 
  "dailyMaxLimit": 0, 
  "exchangeRate": "string", 
  "expireTime": 0, 
  "forceToOthers": true, 
  "hot": true, 
  "isAlreadyBuy": 0, 
  "langSorts": [ 
    "string" 
  ], 


---

## Page 111

sapi-v7.4.md
2024-05-08
111 / 419
  "logoUrl": "string", 
  "order": 0, 
  "perTimeMaxLimit": 0, 
  "perTimeMinLimit": 0, 
  "showRemark": true, 
  "size": "string", 
  "stable": true, 
  "subSelector": [ 
    { 
      "assetCode": "string", 
      "assetName": "string", 
      "dailyMaxLimit": 0, 
      "exchangeRate": "string", 
      "expireTime": 0, 
      "forceToOthers": true, 
      "hot": true, 
      "isAlreadyBuy": 0, 
      "langSorts": [ 
        "string" 
      ], 
      "logoUrl": "string", 
      "order": 0, 
      "perTimeMaxLimit": 0, 
      "perTimeMinLimit": 0, 
      "showRemark": true, 
      "size": "string", 
      "stable": true, 
      "subSelector": [ 
        { 
          "assetCode": "string", 
          "assetName": "string", 
          "dailyMaxLimit": 0, 
          "exchangeRate": "string", 
          "expireTime": 0, 
          "forceToOthers": true, 
          "hot": true, 
          "isAlreadyBuy": 0, 
          "langSorts": [ 
            "string" 
          ], 
          "logoUrl": "string", 
          "order": 0, 
          "perTimeMaxLimit": 0, 
          "perTimeMinLimit": 0, 
          "showRemark": true, 
          "size": "string", 
          "stable": true, 
          "subSelector": [ 
            {} 
          ] 
        } 
      ] 
    } 
  ] 
} 
 
FiatChannelProductSelector
42.185. Properties
Name
Type
Required
Restrictions
Description
assetCode
string
false
none
数字币种
assetName
string
false
none
币种name
dailyMaxLimit
number
false
none
单⽇最⼤限额
exchangeRate
string
false
none
换算汇率
expireTime
integer(int32)
false
none
报价过期时间
forceToOthers
boolean
false
none
none
hot
boolean
false
none
none
isAlreadyBuy
integer(int32)
false
none
⽤户是否已经购买 0-未购买 1-已购买
langSorts
[string]
false
none
语⾔排序，优先级⾼于sortOrder
logoUrl
string
false
none
logo


---

## Page 112

sapi-v7.4.md
2024-05-08
112 / 419
Name
Type
Required
Restrictions
Description
order
integer(int32)
false
none
选择项排序，数值越⼩越优先
perTimeMaxLimit
number
false
none
币种的最⼤上限
perTimeMinLimit
number
false
none
币种的最⼩限额
showRemark
boolean
false
none
是否显示描述⽂案
size
string
false
none
步⻓
stable
boolean
false
none
none
subSelector
[FiatChannelProductSelector]
false
none
⼦选择器
FiatDepositLogVo
{ 
  "amount": 0, 
  "asset": "string", 
  "brokerSubAccountId": "string", 
  "clientDepositId": "string", 
  "createTime": 0, 
  "depositId": 0, 
  "status": "string", 
  "updateTime": 0 
} 
 
FiatDepositLogVo
42.186. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
brokerSubAccountId
string
false
none
none
clientDepositId
string
false
none
none
createTime
integer(int64)
false
none
none
depositId
integer(int64)
false
none
none
status
string
false
none
none
updateTime
integer(int64)
false
none
none
FiatDepositResponse
{ 
  "clientDepositId": "string", 
  "depositId": 0, 
  "status": "string" 
} 
 
FiatDepositResponse
42.187. Properties
Name
Type
Required
Restrictions
Description
clientDepositId
string
false
none
none
depositId
integer(int64)
false
none
none
status
string
false
none
none
FiatUserDetailResp
{ 
  "bindMobileStatus": "BIND", 
  "businessStatus": 0, 


---

## Page 113

sapi-v7.4.md
2024-05-08
113 / 419
  "countryCode": "string", 
  "existsNickname": true, 
  "fiatProtocolConfirm": true, 
  "isSubUser": true, 
  "isUserGoogle": true, 
  "isUserMobile": true, 
  "kycFullName": "string", 
  "kycPassed": true, 
  "kycType": 0, 
  "nickname": "string", 
  "overComplained": 0, 
  "registerDays": 0, 
  "userKycStatus": "NOTVERIFIED" 
} 
 
FiatUserDetailResp
42.188. Properties
Name
Type
Required
Restrictions
Description
bindMobileStatus
string
false
none
If user has bind mobile number (BIND, UNBIND)
businessStatus
integer(int32)
false
none
P2P Business status: (1ÏOpen, 2: Closed, 3: Take break)
countryCode
string
false
none
KYC country code
existsNickname
boolean
false
none
If user set nickname
fiatProtocolConfirm
boolean
false
none
If user has signed the agreement
isSubUser
boolean
false
none
If user is sub-account
isUserGoogle
boolean
false
none
If user has enabled Google 2FA
isUserMobile
boolean
false
none
If user passes mobile verification
kycFullName
string
false
none
Kyc full name
kycPassed
boolean
false
none
If user has passed KYC verification
kycType
integer(int32)
false
none
KYC verification type, (1: Individual, 2: Cooperate)
nickname
string
false
none
Nickname
overComplained
integer(int32)
false
none
Exceed number of complaints. 1ÏYes, 0ÏNo
registerDays
integer(int32)
false
none
User registration days
userKycStatus
string
false
none
Kyc status (1: PASSED)
42.188.1. Enumerated Values
Property
Value
bindMobileStatus
BIND
bindMobileStatus
BIND_CHINA
bindMobileStatus
UNBIND
userKycStatus
NOTVERIFIED
userKycStatus
PASS
userKycStatus
PENDING
userKycStatus
REFUSE
userKycStatus
UNKNOWN
FiatWithdrawLogVo
{ 
  "amount": 0, 
  "asset": "string", 
  "brokerSubAccountId": "string", 
  "clientWithdrawId": "string", 
  "commission": 0, 
  "commissionSubAccountId": "string", 
  "createTime": 0, 
  "status": "string", 


---

## Page 114

sapi-v7.4.md
2024-05-08
114 / 419
  "updateTime": 0, 
  "withdrawId": 0 
} 
 
FiatWithdrawLogVo
42.189. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
brokerSubAccountId
string
false
none
none
clientWithdrawId
string
false
none
none
commission
number
false
none
none
commissionSubAccountId
string
false
none
none
createTime
integer(int64)
false
none
none
status
string
false
none
none
updateTime
integer(int64)
false
none
none
withdrawId
integer(int64)
false
none
none
FiatWithdrawResponse
{ 
  "clientWithdrawId": "string", 
  "status": "string", 
  "withdrawId": 0 
} 
 
FiatWithdrawResponse
42.190. Properties
Name
Type
Required
Restrictions
Description
clientWithdrawId
string
false
none
none
status
string
false
none
none
withdrawId
integer(int64)
false
none
none
FixedPositionChangeResp
{ 
  "clientPurchaseId": "string", 
  "dailyPurchaseId": 0, 
  "success": true, 
  "timestamp": 0 
} 
 
FixedPositionChangeResp
42.191. Properties
Name
Type
Required
Restrictions
Description
clientPurchaseId
string
false
none
none
dailyPurchaseId
integer(int64)
false
none
none
success
boolean
false
none
none
timestamp
integer(int64)
false
none
none
FlexCollateralAssetsDataForSapiResp


---

## Page 115

sapi-v7.4.md
2024-05-08
115 / 419
{ 
  "collateralCoin": "string", 
  "initialLTV": 0, 
  "liquidationLTV": 0, 
  "marginCallLTV": 0, 
  "maxLimit": 0 
} 
 
FlexCollateralAssetsDataForSapiResp
42.192. Properties
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
none
initialLTV
number
false
none
none
liquidationLTV
number
false
none
none
marginCallLTV
number
false
none
none
maxLimit
number
false
none
none
FlexIsoAdjustCollateralHistoryResp
{ 
  "adjustTime": 0, 
  "afterLTV": 0, 
  "collateralAmount": 0, 
  "collateralCoin": "string", 
  "direction": "string", 
  "loanCoin": "string", 
  "preLTV": 0 
} 
 
FlexIsoAdjustCollateralHistoryResp
42.193. Properties
Name
Type
Required
Restrictions
Description
adjustTime
integer(int64)
false
none
none
afterLTV
number
false
none
none
collateralAmount
number
false
none
none
collateralCoin
string
false
none
none
direction
string
false
none
none
loanCoin
string
false
none
none
preLTV
number
false
none
none
FlexIsoAdjustCollateralResp
{ 
  "amount": 0, 
  "collateralCoin": "string", 
  "currentLTV": 0, 
  "direction": "string", 
  "loanCoin": "string", 
  "status": "string" 
} 
 
FlexIsoAdjustCollateralResp
42.194. Properties
Name
Type
Required
Restrictions
Description


---

## Page 116

sapi-v7.4.md
2024-05-08
116 / 419
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
collateralCoin
string
false
none
none
currentLTV
number
false
none
none
direction
string
false
none
none
loanCoin
string
false
none
none
status
string
false
none
none
FlexIsoBorrowHistoryResp
{ 
  "borrowTime": 0, 
  "collateralCoin": "string", 
  "initialCollateralAmount": 0, 
  "initialLoanAmount": 0, 
  "loanCoin": "string", 
  "status": "string" 
} 
 
FlexIsoBorrowHistoryResp
42.195. Properties
Name
Type
Required
Restrictions
Description
borrowTime
integer(int64)
false
none
borrow time
collateralCoin
string
false
none
collateral coin
initialCollateralAmount
number
false
none
initial collateral amount
initialLoanAmount
number
false
none
initial loan amount
loanCoin
string
false
none
loan coin
status
string
false
none
status
FlexIsoBorrowResp
{ 
  "collateralAmount": 0, 
  "collateralCoin": "string", 
  "loanAmount": 0, 
  "loanCoin": "string", 
  "status": "string" 
} 
 
FlexIsoBorrowResp
42.196. Properties
Name
Type
Required
Restrictions
Description
collateralAmount
number
false
none
none
collateralCoin
string
false
none
none
loanAmount
number
false
none
none
loanCoin
string
false
none
none
status
string
false
none
none
FlexIsoCollateralAssetsDataForSapiResp
{ 
  "collateralCoin": "string", 
  "initialLTV": 0, 
  "liquidationLTV": 0, 


---

## Page 117

sapi-v7.4.md
2024-05-08
117 / 419
  "marginCallLTV": 0, 
  "maxLimit": 0 
} 
 
FlexIsoCollateralAssetsDataForSapiResp
42.197. Properties
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
none
initialLTV
number
false
none
none
liquidationLTV
number
false
none
none
marginCallLTV
number
false
none
none
maxLimit
number
false
none
none
FlexIsoLoanableAssetsDataForSapiResp
{ 
  "flexibleInterestRate": 0, 
  "flexibleMaxLimit": 0, 
  "flexibleMinLimit": 0, 
  "loanCoin": "string" 
} 
 
FlexIsoLoanableAssetsDataForSapiResp
42.198. Properties
Name
Type
Required
Restrictions
Description
flexibleInterestRate
number
false
none
none
flexibleMaxLimit
number
false
none
none
flexibleMinLimit
number
false
none
none
loanCoin
string
false
none
none
FlexIsoOngoingOrderResp
{ 
  "collateralAmount": 0, 
  "collateralCoin": "string", 
  "currentLTV": 0, 
  "loanCoin": "string", 
  "totalDebt": 0 
} 
 
FlexIsoOngoingOrderResp
42.199. Properties
Name
Type
Required
Restrictions
Description
collateralAmount
number
false
none
collateral Amount
collateralCoin
string
false
none
collateral coin
currentLTV
number
false
none
ltv
loanCoin
string
false
none
loan coin
totalDebt
number
false
none
total Debt
FlexIsoRepayHistoryResp
{ 
  "collateralCoin": "string", 


---

## Page 118

sapi-v7.4.md
2024-05-08
118 / 419
  "collateralReturn": 0, 
  "loanCoin": "string", 
  "repayAmount": 0, 
  "repayStatus": "string", 
  "repayTime": 0 
} 
 
FlexIsoRepayHistoryResp
42.200. Properties
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
collateral coin
collateralReturn
number
false
none
collateral return
loanCoin
string
false
none
loan coin
repayAmount
number
false
none
repay amount
repayStatus
string
false
none
repay status
repayTime
integer(int64)
false
none
repay time
FlexIsoRepayResp
{ 
  "collateralCoin": "string", 
  "currentLTV": 0, 
  "fullRepayment": true, 
  "loanCoin": "string", 
  "remainingCollateral": 0, 
  "remainingDebt": 0, 
  "repayStatus": "string" 
} 
 
FlexIsoRepayResp
42.201. Properties
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
none
currentLTV
number
false
none
none
fullRepayment
boolean
false
none
none
loanCoin
string
false
none
none
remainingCollateral
number
false
none
none
remainingDebt
number
false
none
none
repayStatus
string
false
none
none
FlexLineCreditAccountInfoResp
{ 
  "availableCreditLimit": 0, 
  "eligibleSpotAsset": 0, 
  "riskLevel": 0, 
  "spotAsset": 0, 
  "totalCreditLimit": 0, 
  "totalUnpaidInterest": 0, 
  "usedCreditLimit": 0, 
  "vipLoan": 0 
} 
 
FlexLineCreditAccountInfoResp
42.202. Properties


---

## Page 119

sapi-v7.4.md
2024-05-08
119 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
availableCreditLimit
number
false
none
none
eligibleSpotAsset
number
false
none
none
riskLevel
number
false
none
none
spotAsset
number
false
none
none
totalCreditLimit
number
false
none
none
totalUnpaidInterest
number
false
none
none
usedCreditLimit
number
false
none
none
vipLoan
number
false
none
none
FlexLoanableAssetsDataForSapiResp
{ 
  "flexibleInterestRate": 0, 
  "flexibleMaxLimit": 0, 
  "flexibleMinLimit": 0, 
  "loanCoin": "string" 
} 
 
FlexLoanableAssetsDataForSapiResp
42.203. Properties
Name
Type
Required
Restrictions
Description
flexibleInterestRate
number
false
none
none
flexibleMaxLimit
number
false
none
none
flexibleMinLimit
number
false
none
none
loanCoin
string
false
none
none
FlexibleProductResp
{ 
  "airDropPercentageRate": 0, 
  "asset": "string", 
  "canPurchase": true, 
  "canRedeem": true, 
  "hot": true, 
  "isSoldOut": true, 
  "latestAnnualPercentageRate": 0, 
  "minPurchaseAmount": 0, 
  "productId": "string", 
  "status": "CREATED", 
  "subscriptionStartTime": 0, 
  "tierAnnualPercentageRate": { 
    "property1": "string", 
    "property2": "string" 
  } 
} 
 
FlexibleProductResp
42.204. Properties
Name
Type
Required
Restrictions
Description
airDropPercentageRate
number
false
none
Airdrop APR
asset
string
false
none
asset
canPurchase
boolean
false
none
申购状态: 开启、关闭
canRedeem
boolean
false
none
赎回状态: 开启、关闭
hot
boolean
false
none
hot push


---

## Page 120

sapi-v7.4.md
2024-05-08
120 / 419
Name
Type
Required
Restrictions
Description
isSoldOut
boolean
false
none
sold out status
latestAnnualPercentageRate
number
false
none
market apr
minPurchaseAmount
number
false
none
最⼩申购额度
productId
string
false
none
product id
status
string
false
none
项⽬状态: 0新建、10预热中、20申购中、30结束
subscriptionStartTime
integer(int64)
false
none
subscription start time
tierAnnualPercentageRate
object
false
none
Bonus Tiered APR
» additionalProperties
string
false
none
none
42.204.1. Enumerated Values
Property
Value
status
CREATED
status
END
status
PREHEATING
status
PURCHASING
ForceOrderResp
{ 
  "avgPrice": 0, 
  "executedQty": 0, 
  "isIsolated": true, 
  "orderId": 0, 
  "price": 0, 
  "qty": 0, 
  "side": "BUY", 
  "symbol": "string", 
  "time": 0, 
  "timeInForce": "FOK", 
  "updatedTime": 0 
} 
 
ForceOrderResp
42.205. Properties
Name
Type
Required
Restrictions
Description
avgPrice
number
false
none
none
executedQty
number
false
none
none
isIsolated
boolean
false
none
none
orderId
integer(int64)
false
none
none
price
number
false
none
none
qty
number
false
none
none
side
string
false
none
none
symbol
string
false
none
none
time
integer(int64)
false
none
none
timeInForce
string
false
none
none
updatedTime
integer(int64)
false
none
none
42.205.1. Enumerated Values
Property
Value
side
BUY
side
SELL


---

## Page 121

sapi-v7.4.md
2024-05-08
121 / 419
Property
Value
timeInForce
FOK
timeInForce
GTC
timeInForce
IOC
FreezeAssetResp
{ 
  "errorCode": "string", 
  "errorMessage": "string", 
  "status": "string" 
} 
 
FreezeAssetResp
42.206. Properties
Name
Type
Required
Restrictions
Description
errorCode
string
false
none
失败错误码
errorMessage
string
false
none
失败错误描述
status
string
false
none
状态
FundFlowResp
{ 
  "amount": 0, 
  "asset": "string", 
  "timestamp": 0, 
  "tranId": "string", 
  "type": "string" 
} 
 
FundFlowResp
42.207. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
⾦额
asset
string
false
none
币种
timestamp
integer(int64)
false
none
时间戳
tranId
string
false
none
tranid
type
string
false
none
类型
FutureAccountSummaryInfoVoSapiVersion
{ 
  "asset": "string", 
  "email": "string", 
  "totalInitialMargin": "string", 
  "totalMaintenanceMargin": "string", 
  "totalMarginBalance": "string", 
  "totalOpenOrderInitialMargin": "string", 
  "totalPositionInitialMargin": "string", 
  "totalUnrealizedProfit": "string", 
  "totalWalletBalance": "string" 
} 
 
FutureAccountSummaryInfoVoSapiVersion
42.208. Properties


---

## Page 122

sapi-v7.4.md
2024-05-08
122 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
email
string
false
none
none
totalInitialMargin
string
false
none
none
totalMaintenanceMargin
string
false
none
none
totalMarginBalance
string
false
none
none
totalOpenOrderInitialMargin
string
false
none
none
totalPositionInitialMargin
string
false
none
none
totalUnrealizedProfit
string
false
none
none
totalWalletBalance
string
false
none
none
FutureAssetRiskInfoVo
{ 
  "asset": "string", 
  "initialMargin": "string", 
  "maintenanceMargin": "string", 
  "marginBalance": "string", 
  "maxWithdrawAmount": "string", 
  "openOrderInitialMargin": "string", 
  "positionInitialMargin": "string", 
  "unrealizedProfit": "string", 
  "updateTime": 0, 
  "walletBalance": "string" 
} 
 
FutureAssetRiskInfoVo
42.209. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
initialMargin
string
false
none
none
maintenanceMargin
string
false
none
none
marginBalance
string
false
none
none
maxWithdrawAmount
string
false
none
none
openOrderInitialMargin
string
false
none
none
positionInitialMargin
string
false
none
none
unrealizedProfit
string
false
none
none
updateTime
integer(int64)
false
none
none
walletBalance
string
false
none
none
FuturePositionRiskVO
{ 
  "entryPrice": "string", 
  "leverage": "string", 
  "liquidationPrice": "string", 
  "markPrice": "string", 
  "maxNotional": "string", 
  "positionAmount": "string", 
  "symbol": "string", 
  "unrealizedProfit": "string" 
} 
 
FuturePositionRiskVO
42.210. Properties


---

## Page 123

sapi-v7.4.md
2024-05-08
123 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
entryPrice
string
false
none
avg cost of that position
leverage
string
false
none
liquidation price
liquidationPrice
string
false
none
liquidation price
markPrice
string
false
none
mark price of that position
maxNotional
string
false
none
max notional value
positionAmount
string
false
none
position amount
symbol
string
false
none
symbol name
unrealizedProfit
string
false
none
unrealized pnl of that position
FutureTransferHistoryResp
{ 
  "amount": 0, 
  "asset": "string", 
  "clientTranId": "string", 
  "status": "CONFIRMED", 
  "timestamp": 0, 
  "tranId": 0, 
  "type": 0 
} 
 
FutureTransferHistoryResp
42.211. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
划转⾦额
asset
string
false
none
资产名称
clientTranId
string
false
none
业务唯⼀ID
status
string
false
none
状态
timestamp
integer(int64)
false
none
划转时间
tranId
integer(int64)
false
none
划转ID
type
integer(int32)
false
none
划转类型
42.211.1. Enumerated Values
Property
Value
status
CONFIRMED
status
FAILED
status
PENDING
FuturesDataDownloadLinkVo
{ 
  "day": "string", 
  "url": "string" 
} 
 
FuturesDataDownloadLinkVo
42.212. Properties
Name
Type
Required
Restrictions
Description
day
string
false
none
none
url
string
false
none
none


---

## Page 124

sapi-v7.4.md
2024-05-08
124 / 419
FuturesHistDataDownloadLinkResp
{ 
  "expirationTime": 0, 
  "link": "string" 
} 
 
FuturesHistDataDownloadLinkResp
42.213. Properties
Name
Type
Required
Restrictions
Description
expirationTime
integer(int64)
false
none
the link would expire after this timestamp
link
string
false
none
download link
FuturesHistDataIdResp
{ 
  "id": 0 
} 
 
FuturesHistDataIdResp
42.214. Properties
Name
Type
Required
Restrictions
Description
id
integer(int64)
false
none
downloadId
FuturesVipDownloadLinkResp
{ 
  "data": [ 
    { 
      "day": "string", 
      "url": "string" 
    } 
  ] 
} 
 
FuturesVipDownloadLinkResp
42.215. Properties
Name
Type
Required
Restrictions
Description
data
[FuturesDataDownloadLinkVo]
false
none
none
GenApiAgentDownloadUrlResp
{ 
  "code": 0, 
  "msg": "string" 
} 
 
GenApiAgentDownloadUrlResp
42.216. Properties
Name
Type
Required
Restrictions
Description
code
integer(int32)
false
none
none
msg
string
false
none
none


---

## Page 125

sapi-v7.4.md
2024-05-08
125 / 419
GetAddressResp
{ 
  "address": "string", 
  "coin": "string", 
  "isDefault": 0, 
  "networkSet": [ 
    "string" 
  ], 
  "tag": "string", 
  "url": "string" 
} 
 
GetAddressResp
42.217. Properties
Name
Type
Required
Restrictions
Description
address
string
false
none
none
coin
string
false
none
none
isDefault
integer(int32)
false
none
是否默认地址,1为默认地址
networkSet
[string]
false
none
none
tag
string
false
none
none
url
string
false
none
none
GetAvailableAssetResp
{ 
  "assets": [ 
    "string" 
  ] 
} 
 
GetAvailableAssetResp
42.218. Properties
Name
Type
Required
Restrictions
Description
assets
[string]
false
none
none
GetFiatChannelProductSelectorResponse
{ 
  "buySelector": [ 
    { 
      "assetCode": "string", 
      "assetName": "string", 
      "dailyMaxLimit": 0, 
      "exchangeRate": "string", 
      "expireTime": 0, 
      "forceToOthers": true, 
      "hot": true, 
      "isAlreadyBuy": 0, 
      "langSorts": [ 
        "string" 
      ], 
      "logoUrl": "string", 
      "order": 0, 
      "perTimeMaxLimit": 0, 
      "perTimeMinLimit": 0, 
      "showRemark": true, 
      "size": "string", 
      "stable": true, 
      "subSelector": [ 
        { 
          "assetCode": "string", 


---

## Page 126

sapi-v7.4.md
2024-05-08
126 / 419
          "assetName": "string", 
          "dailyMaxLimit": 0, 
          "exchangeRate": "string", 
          "expireTime": 0, 
          "forceToOthers": true, 
          "hot": true, 
          "isAlreadyBuy": 0, 
          "langSorts": [ 
            "string" 
          ], 
          "logoUrl": "string", 
          "order": 0, 
          "perTimeMaxLimit": 0, 
          "perTimeMinLimit": 0, 
          "showRemark": true, 
          "size": "string", 
          "stable": true, 
          "subSelector": [ 
            {} 
          ] 
        } 
      ] 
    } 
  ], 
  "sellSelector": [ 
    { 
      "assetCode": "string", 
      "assetName": "string", 
      "dailyMaxLimit": 0, 
      "exchangeRate": "string", 
      "expireTime": 0, 
      "forceToOthers": true, 
      "hot": true, 
      "isAlreadyBuy": 0, 
      "langSorts": [ 
        "string" 
      ], 
      "logoUrl": "string", 
      "order": 0, 
      "perTimeMaxLimit": 0, 
      "perTimeMinLimit": 0, 
      "showRemark": true, 
      "size": "string", 
      "stable": true, 
      "subSelector": [ 
        { 
          "assetCode": "string", 
          "assetName": "string", 
          "dailyMaxLimit": 0, 
          "exchangeRate": "string", 
          "expireTime": 0, 
          "forceToOthers": true, 
          "hot": true, 
          "isAlreadyBuy": 0, 
          "langSorts": [ 
            "string" 
          ], 
          "logoUrl": "string", 
          "order": 0, 
          "perTimeMaxLimit": 0, 
          "perTimeMinLimit": 0, 
          "showRemark": true, 
          "size": "string", 
          "stable": true, 
          "subSelector": [ 
            {} 
          ] 
        } 
      ] 
    } 
  ] 
} 
 
GetFiatChannelProductSelectorResponse
42.219. Properties
Name
Type
Required
Restrictions
Description


---

## Page 127

sapi-v7.4.md
2024-05-08
127 / 419
Name
Type
Required
Restrictions
Description
buySelector
[FiatChannelProductSelector]
false
none
购买下拉框
sellSelector
[FiatChannelProductSelector]
false
none
卖出下拉框
GetIfsApplyResp
{ 
  "details": [ 
    { 
      "apr": 0, 
      "asset": "string", 
      "canPurchase": true, 
      "duration": 0, 
      "extraRewardAPR": 0, 
      "extraRewardAsset": "string", 
      "isSoldOut": true, 
      "renewable": true, 
      "rewardAsset": "string", 
      "status": "string", 
      "subscriptionStartTime": 0 
    } 
  ], 
  "direction": "string", 
  "execStatus": "string", 
  "id": 0, 
  "status": "string" 
} 
 
GetIfsApplyResp
42.220. Properties
Name
Type
Required
Restrictions
Description
details
[Detail]
false
none
none
direction
string
false
none
借/还
execStatus
string
false
none
划转状态
id
integer(int64)
false
none
none
status
string
false
none
审批状态
GetSubAccountTransferHistoryResp
{ 
  "msg": "string", 
  "success": true, 
  "transfers": [ 
    { 
      "asset": "string", 
      "from": "string", 
      "qty": "string", 
      "status": "string", 
      "time": 0, 
      "to": "string", 
      "tranId": 0 
    } 
  ] 
} 
 
GetSubAccountTransferHistoryResp
42.221. Properties
Name
Type
Required
Restrictions
Description
msg
string
false
none
none
success
boolean
false
none
none
transfers
[GetSubUserTransferHistoryResponse]
false
none
[GetSubUserTransferHistoryResponse]


---

## Page 128

sapi-v7.4.md
2024-05-08
128 / 419
GetSubUserTransferHistoryResponse
{ 
  "asset": "string", 
  "from": "string", 
  "qty": "string", 
  "status": "string", 
  "time": 0, 
  "to": "string", 
  "tranId": 0 
} 
 
GetSubUserTransferHistoryResponse
42.222. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
from
string
false
none
none
qty
string
false
none
none
status
string
false
none
none
time
integer(int64)
false
none
none
to
string
false
none
none
tranId
integer(int64)
false
none
none
GetSubUserTransferHistoryVersionForSubUserResponse
{ 
  "asset": "string", 
  "counterParty": "string", 
  "email": "string", 
  "fromAccountType": "string", 
  "qty": "string", 
  "status": "string", 
  "time": 0, 
  "toAccountType": "string", 
  "tranId": 0, 
  "type": 0 
} 
 
GetSubUserTransferHistoryVersionForSubUserResponse
42.223. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
counterParty
string
false
none
none
email
string
false
none
none
fromAccountType
string
false
none
none
qty
string
false
none
none
status
string
false
none
none
time
integer(int64)
false
none
none
toAccountType
string
false
none
none
tranId
integer(int64)
false
none
none
type
integer(int32)
false
none
none
GetSystemFundResp


---

## Page 129

sapi-v7.4.md
2024-05-08
129 / 419
{ 
  "details": [ 
    { 
      "apr": 0, 
      "asset": "string", 
      "canPurchase": true, 
      "duration": 0, 
      "extraRewardAPR": 0, 
      "extraRewardAsset": "string", 
      "isSoldOut": true, 
      "renewable": true, 
      "rewardAsset": "string", 
      "status": "string", 
      "subscriptionStartTime": 0 
    } 
  ] 
} 
 
GetSystemFundResp
42.224. Properties
Name
Type
Required
Restrictions
Description
details
[Detail]
false
none
none
GetUniversalTransferHistoryResponse
{ 
  "result": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "clientTranId": "string", 
      "createTimeStamp": 0, 
      "fromAccountType": "string", 
      "fromEmail": "string", 
      "status": "string", 
      "toAccountType": "string", 
      "toEmail": "string", 
      "tranId": 0 
    } 
  ], 
  "totalCount": 0 
} 
 
GetUniversalTransferHistoryResponse
42.225. Properties
Name
Type
Required
Restrictions
Description
result
[UniversalTransferHistoryInfoVo]
false
none
[UniversalTransferHistoryInfoVo]
totalCount
integer(int64)
false
none
none
InstrumentDefinitionResp
{ 
  "productId": 0, 
  "symbol": "string" 
} 
 
InstrumentDefinitionResp
42.226. Properties
Name
Type
Required
Restrictions
Description
productId
integer(int64)
false
none
none


---

## Page 130

sapi-v7.4.md
2024-05-08
130 / 419
Name
Type
Required
Restrictions
Description
symbol
string
false
none
none
InterestHistoryResp
{ 
  "asset": "string", 
  "interest": 0, 
  "interestAccruedTime": 0, 
  "interestRate": 0, 
  "principal": 0 
} 
 
InterestHistoryResp
42.227. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
interest
number
false
none
none
interestAccruedTime
integer(int64)
false
none
none
interestRate
number
false
none
none
principal
number
false
none
none
InterestRateResponse
{ 
  "asset": "string", 
  "dailyInterest": 0, 
  "yearlyInterest": 0 
} 
 
InterestRateResponse
42.228. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
dailyInterest
number
false
none
none
yearlyInterest
number
false
none
none
IsolatedAccountDetailResp
{ 
  "assets": [ 
    { 
      "baseAsset": { 
        "userId": 0, 
        "value": 0 
      }, 
      "enabled": true, 
      "indexPrice": 0, 
      "isolatedCreated": true, 
      "liquidatePrice": 0, 
      "liquidateRate": 0, 
      "marginLevel": 0, 
      "marginLevelStatus": "string", 
      "marginRatio": 0, 
      "quoteAsset": { 
        "userId": 0, 
        "value": 0 
      }, 
      "symbol": "string", 
      "tradeEnabled": true 


---

## Page 131

sapi-v7.4.md
2024-05-08
131 / 419
    } 
  ], 
  "totalAssetOfBtc": 0, 
  "totalLiabilityOfBtc": 0, 
  "totalNetAssetOfBtc": 0 
} 
 
IsolatedAccountDetailResp
42.229. Properties
Name
Type
Required
Restrictions
Description
assets
[AccountDetail]
false
none
none
totalAssetOfBtc
number
false
none
none
totalLiabilityOfBtc
number
false
none
none
totalNetAssetOfBtc
number
false
none
none
IsolatedAccountLimitConfigResp
{ 
  "enabledAccount": 0, 
  "maxAccount": 0 
} 
 
IsolatedAccountLimitConfigResp
42.230. Properties
Name
Type
Required
Restrictions
Description
enabledAccount
integer(int32)
false
none
none
maxAccount
integer(int32)
false
none
none
IsolatedAssetFee
{ 
  "borrowLimit": 0, 
  "coin": "string", 
  "dailyInterest": 0 
} 
 
IsolatedAssetFee
42.231. Properties
Name
Type
Required
Restrictions
Description
borrowLimit
number
false
none
none
coin
string
false
none
none
dailyInterest
number
false
none
none
IsolatedMarginPairResp
{ 
  "base": "string", 
  "delistTime": 0, 
  "isBuyAllowed": true, 
  "isMarginTrade": true, 
  "isSellAllowed": true, 
  "quote": "string", 
  "symbol": "string" 
} 
 


---

## Page 132

sapi-v7.4.md
2024-05-08
132 / 419
IsolatedMarginPairResp
42.232. Properties
Name
Type
Required
Restrictions
Description
base
string
false
none
none
delistTime
integer(int64)
false
none
none
isBuyAllowed
boolean
false
none
none
isMarginTrade
boolean
false
none
none
isSellAllowed
boolean
false
none
none
quote
string
false
none
none
symbol
string
false
none
none
JexCommonResp
{ 
  "code": 0, 
  "data": {}, 
  "msg": "string" 
} 
 
JexCommonResp
42.233. Properties
Name
Type
Required
Restrictions
Description
code
integer(int32)
false
none
none
data
object
false
none
none
msg
string
false
none
none
LedgerTransferPageResp
{ 
  "amount": 0, 
  "asset": "string", 
  "createTime": "2019-08-24T14:15:22Z", 
  "status": "string", 
  "tranId": 0, 
  "type": 0 
} 
 
LedgerTransferPageResp
42.234. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
数量
asset
string
false
none
币种
createTime
string(date-time)
false
none
创建时间
status
string
false
none
状态:P-处理中, S-成功,F失败
tranId
integer(int64)
false
none
流⽔号
type
integer(int32)
false
none
交易类型
LeftQuotaResp
{ 
  "asset": "string", 
  "leftQuota": 0 


---

## Page 133

sapi-v7.4.md
2024-05-08
133 / 419
} 
 
LeftQuotaResp
42.235. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
leftQuota
number
false
none
none
LendingAssetResp
{ 
  "assets": { 
    "property1": 0, 
    "property2": 0 
  }, 
  "updateTime": 0 
} 
 
LendingAssetResp
42.236. Properties
Name
Type
Required
Restrictions
Description
assets
object
false
none
none
» additionalProperties
number
false
none
none
updateTime
integer(int64)
false
none
none
LeverageBracket
{ 
  "fastNum": 0, 
  "initialMarginRate": 0, 
  "leverage": 0, 
  "maintenanceMarginRate": 0, 
  "maxDebt": 0 
} 
 
LeverageBracket
42.237. Properties
Name
Type
Required
Restrictions
Description
fastNum
number
false
none
速算数
initialMarginRate
number
false
none
初始保证⾦率
leverage
integer(int32)
false
none
杠杆倍数
maintenanceMarginRate
number
false
none
维持保证⾦率
maxDebt
number
false
none
最⼤负债
LightningInvoiceReq
{ 
  "invoice": "string", 
  "type": 0 
} 
 
LightningInvoiceReq


---

## Page 134

sapi-v7.4.md
2024-05-08
134 / 419
42.238. Properties
Name
Type
Required
Restrictions
Description
invoice
string
false
none
none
type
integer(int32)
false
none
类型:0-外部,1-平台
LightningInvoiceResp
{ 
  "amount": "string", 
  "expireMillis": 0, 
  "internal": true, 
  "routable": true 
} 
 
LightningInvoiceResp
42.239. Properties
Name
Type
Required
Restrictions
Description
amount
string
false
none
none
expireMillis
integer(int64)
false
none
none
internal
boolean
false
none
none
routable
boolean
false
none
none
Liquidity
{ 
  "constantA": 0, 
  "minRedeemShare": 0, 
  "slippageTolerance": 0 
} 
 
Liquidity
42.240. Properties
Name
Type
Required
Restrictions
Description
constantA
number
false
none
none
minRedeemShare
number
false
none
none
slippageTolerance
number
false
none
none
LiquidityAmount
{ 
  "amount": 0, 
  "asset": "string" 
} 
 
LiquidityAmount
42.241. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
ListConfirmedOrderResp


---

## Page 135

sapi-v7.4.md
2024-05-08
135 / 419
{ 
  "hasNext": true, 
  "list": [ 
    { 
      "clientOrderId": "string", 
      "code": 0, 
      "confirmedTime": 0, 
      "createTime": 0, 
      "expiryTime": 0, 
      "msg": "string", 
      "orderId": 0, 
      "orderStatus": "string", 
      "price": 0, 
      "quantity": 0, 
      "quoteAsset": "string", 
      "settleTime": 0, 
      "strikePrice": 0, 
      "timeInForce": "string", 
      "type": "string", 
      "underlying": "string" 
    } 
  ] 
} 
 
ListConfirmedOrderResp
42.242. Properties
Name
Type
Required
Restrictions
Description
hasNext
boolean
false
none
none
list
[Order0]
false
none
none
ListenKeyResp
{ 
  "listenKey": "string" 
} 
 
ListenKeyResp
42.243. Properties
Name
Type
Required
Restrictions
Description
listenKey
string
false
none
none
LoanCCAdjustCollateralHistoryResp
{ 
  "adjustTime": 0, 
  "afterCollateralRate": 0, 
  "amount": 0, 
  "coin": "string", 
  "collateralCoin": "string", 
  "direction": "ADDITIONAL", 
  "preCollateralRate": 0, 
  "status": "COMPLETED" 
} 
 
LoanCCAdjustCollateralHistoryResp
42.244. Properties
Name
Type
Required
Restrictions
Description
adjustTime
integer(int64)
false
none
调整时间
afterCollateralRate
number
false
none
调整后质押率


---

## Page 136

sapi-v7.4.md
2024-05-08
136 / 419
Name
Type
Required
Restrictions
Description
amount
number
false
none
调整⾦额
coin
string
false
none
借款币种
collateralCoin
string
false
none
抵押币种
direction
string
false
none
调整类型
preCollateralRate
number
false
none
调整前质押率
status
string
false
none
状态
42.244.1. Enumerated Values
Property
Value
direction
ADDITIONAL
direction
REDUCED
status
COMPLETED
status
FAILED
status
PENDING
LoanCCAdjustCollateralResp
{ 
  "amount": 0, 
  "collateralCoin": "string", 
  "direction": "ADDITIONAL", 
  "loanCoin": "string", 
  "time": 0 
} 
 
LoanCCAdjustCollateralResp
42.245. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
调整⾦额
collateralCoin
string
false
none
抵押币种
direction
string
false
none
调整⽅向
loanCoin
string
false
none
借贷币种
time
integer(int64)
false
none
调整时间
42.245.1. Enumerated Values
Property
Value
direction
ADDITIONAL
direction
REDUCED
LoanCCBorrowHistoryResp
{ 
  "borrowId": "string", 
  "coin": "string", 
  "collateralAmount": 0, 
  "collateralCoin": "string", 
  "collateralRate": 0, 
  "confirmedTime": 0, 
  "deadline": 0, 
  "leftPrincipal": 0, 
  "leftTotal": 0, 
  "orderStatus": "string" 
} 
 


---

## Page 137

sapi-v7.4.md
2024-05-08
137 / 419
LoanCCBorrowHistoryResp
42.246. Properties
Name
Type
Required
Restrictions
Description
borrowId
string
false
none
id
coin
string
false
none
借贷币种
collateralAmount
number
false
none
抵押⾦额
collateralCoin
string
false
none
抵押币种
collateralRate
number
false
none
质押率
confirmedTime
integer(int64)
false
none
confirmedTime
deadline
integer(int64)
false
none
deadline
leftPrincipal
number
false
none
剩余总负债本⾦
leftTotal
number
false
none
剩余总负债
orderStatus
string
false
none
订单状态
LoanCCBorrowResp
{ 
  "amount": 0, 
  "borrowId": "string", 
  "coin": "string", 
  "collateralAmount": 0, 
  "collateralCoin": "string", 
  "time": 0 
} 
 
LoanCCBorrowResp
42.247. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
借贷⾦额
borrowId
string
false
none
id
coin
string
false
none
借贷币种
collateralAmount
number
false
none
抵押⾦额
collateralCoin
string
false
none
抵押币种
time
integer(int64)
false
none
time
LoanCCCalcLevelAfterAdjustLtvResp
{ 
  "afterCollateralRate": 0 
} 
 
LoanCCCalcLevelAfterAdjustLtvResp
42.248. Properties
Name
Type
Required
Restrictions
Description
afterCollateralRate
number
false
none
数量
LoanCCCalcMaxAdjustAmountResp
{ 
  "maxInAmount": 0, 
  "maxOutAmount": 0 


---

## Page 138

sapi-v7.4.md
2024-05-08
138 / 419
} 
 
LoanCCCalcMaxAdjustAmountResp
42.249. Properties
Name
Type
Required
Restrictions
Description
maxInAmount
number
false
none
最⼤可转⼊数量
maxOutAmount
number
false
none
最⼤可转出数量
LoanCCCollateralRepayLimitResp
{ 
  "coin": "string", 
  "collateralCoin": "string", 
  "max": 0, 
  "min": 0 
} 
 
LoanCCCollateralRepayLimitResp
42.250. Properties
Name
Type
Required
Restrictions
Description
coin
string
false
none
借贷币种
collateralCoin
string
false
none
抵押币种
max
number
false
none
最⼤
min
number
false
none
最⼩
LoanCCCollateralRepayQuoteResp
{ 
  "amount": 0, 
  "coin": "string", 
  "collateralCoin": "string", 
  "quoteId": "string" 
} 
 
LoanCCCollateralRepayQuoteResp
42.251. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
还款⾦额
coin
string
false
none
借贷币种
collateralCoin
string
false
none
抵押币种
quoteId
string
false
none
quoteId
LoanCCCollateralRepayResp
{ 
  "amount": 0, 
  "coin": "string", 
  "collateralCoin": "string", 
  "quoteId": "string" 
} 
 
LoanCCCollateralRepayResp


---

## Page 139

sapi-v7.4.md
2024-05-08
139 / 419
42.252. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
还款⾦额
coin
string
false
none
借贷币种
collateralCoin
string
false
none
抵押币种
quoteId
string
false
none
quoteId
LoanCCConfigsResp
{ 
  "collateralCoin": "string", 
  "currentCollateralRate": 0, 
  "interestGracePeriod": "string", 
  "interestRate": 0, 
  "liquidationCollateralRate": 0, 
  "loanCoin": "string", 
  "marginCallCollateralRate": 0, 
  "rate": 0 
} 
 
LoanCCConfigsResp
42.253. Properties
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
抵押币种
currentCollateralRate
number
false
none
当前质押率
interestGracePeriod
string
false
none
免息期
interestRate
number
false
none
⽇利率
liquidationCollateralRate
number
false
none
平仓质押率
loanCoin
string
false
none
借贷币种
marginCallCollateralRate
number
false
none
补仓质押率
rate
number
false
none
初始质押率
LoanCCInterestHistoryResp
{ 
  "collateralCoin": "string", 
  "interest": 0, 
  "interestCoin": "string", 
  "interestFreeLimitUsed": 0, 
  "interestRate": 0, 
  "principalForInterest": 0, 
  "time": 0 
} 
 
LoanCCInterestHistoryResp
42.254. Properties
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
抵押币种
interest
number
false
none
利息
interestCoin
string
false
none
计息币种
interestFreeLimitUsed
number
false
none
已使⽤的免息额度
interestRate
number
false
none
⽇利率
principalForInterest
number
false
none
计息本⾦


---

## Page 140

sapi-v7.4.md
2024-05-08
140 / 419
Name
Type
Required
Restrictions
Description
time
integer(int64)
false
none
计息时间
LoanCCLiquidationHistoryResp
{ 
  "coin": "string", 
  "collateralAmountForLiquidation": 0, 
  "collateralCoin": "string", 
  "forceLiquidationStartTime": 0, 
  "restCollateralAmountAfterLiquidation": 0, 
  "restLoanAmount": 0, 
  "status": "CLOSED" 
} 
 
LoanCCLiquidationHistoryResp
42.255. Properties
Name
Type
Required
Restrictions
Description
coin
string
false
none
借款币种
collateralAmountForLiquidation
number
false
none
平仓完成消耗的质押资产⾦额，8位⼩数
collateralCoin
string
false
none
抵押币种
forceLiquidationStartTime
integer(int64)
false
none
强平时间
restCollateralAmountAfterLiquidation
number
false
none
平仓剩余质押⾦额
restLoanAmount
number
false
none
借款⾦额
status
string
false
none
状态
42.255.1. Enumerated Values
Property
Value
status
CLOSED
status
COLLATERAL_TRANSFER_FAILED
status
COLLATERAL_TRANSFER_SUCCESS
status
LIABILITY_TRANSFER_FAILED
status
LIABILITY_TRANSFER_SUCCESS
status
NOTIFY_ENGINE_FAILED
status
NOTIFY_ENGINE_SUCCESS
status
PENDING
status
REFUNDING
status
REPAY_FAILED
LoanCCQueryCollateralRepayResultResp
{ 
  "quoteId": "string", 
  "status": "string" 
} 
 
LoanCCQueryCollateralRepayResultResp
42.256. Properties
Name
Type
Required
Restrictions
Description
quoteId
string
false
none
quoteId
status
string
false
none
状态


---

## Page 141

sapi-v7.4.md
2024-05-08
141 / 419
LoanCCRepayHistoryResp
{ 
  "amount": 0, 
  "coin": "string", 
  "collateralAmount": 0, 
  "collateralCoin": "string", 
  "confirmedTime": 0, 
  "price": 0, 
  "releasedCollateral": 0, 
  "repayCollateral": 0, 
  "repayId": "string", 
  "repayType": "string", 
  "status": "string", 
  "updateTime": 0 
} 
 
LoanCCRepayHistoryResp
42.257. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
还款⾦额
coin
string
false
none
借贷币种
collateralAmount
number
false
none
抵押⾦额
collateralCoin
string
false
none
抵押币种
confirmedTime
integer(int64)
false
none
confirmedTime
price
number
false
none
Loan/collateral exchange rate
releasedCollateral
number
false
none
释放的抵押⾦额
repayCollateral
number
false
none
还款使⽤的抵押⾦
repayId
string
false
none
id
repayType
string
false
none
还款类型
status
string
false
none
状态
updateTime
integer(int64)
false
none
updateTime
LoanCCRepayResp
{ 
  "amount": 0, 
  "coin": "string", 
  "collateralCoin": "string", 
  "repayId": "string" 
} 
 
LoanCCRepayResp
42.258. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
借贷⾦额
coin
string
false
none
借贷币种
collateralCoin
string
false
none
抵押币种
repayId
string
false
none
id
LoanCCWalletDataResp
{ 
  "asset": "string", 
  "crossCollaterals": [ 
    { 


---

## Page 142

sapi-v7.4.md
2024-05-08
142 / 419
      "collateralCoin": "string", 
      "currentCollateralRate": 0, 
      "interest": 0, 
      "interestFreeLimitUsed": 0, 
      "loanAmount": 0, 
      "loanCoin": "string", 
      "locked": 0, 
      "principalForInterest": 0 
    } 
  ], 
  "interestFreeLimit": 0, 
  "totalBorrowed": 0, 
  "totalCrossCollateral": 0, 
  "totalInterest": 0 
} 
 
LoanCCWalletDataResp
42.259. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
借贷币种
crossCollaterals
[Collateral]
false
none
抵押数据
interestFreeLimit
number
false
none
免息额度
totalBorrowed
number
false
none
总借贷⾦额
totalCrossCollateral
number
false
none
总抵押⾦额
totalInterest
number
false
none
总利息
LoanFlexAdjustCollateralHistoryResp
{ 
  "adjustTime": 0, 
  "afterLTV": 0, 
  "collateralAmount": 0, 
  "collateralCoin": "string", 
  "direction": "string", 
  "loanCoin": "string", 
  "preLTV": 0 
} 
 
LoanFlexAdjustCollateralHistoryResp
42.260. Properties
Name
Type
Required
Restrictions
Description
adjustTime
integer(int64)
false
none
none
afterLTV
number
false
none
none
collateralAmount
number
false
none
none
collateralCoin
string
false
none
none
direction
string
false
none
none
loanCoin
string
false
none
none
preLTV
number
false
none
none
LoanFlexAdjustCollateralResp
{ 
  "amount": 0, 
  "collateralCoin": "string", 
  "currentLTV": 0, 
  "direction": "string", 
  "loanCoin": "string" 
} 
 


---

## Page 143

sapi-v7.4.md
2024-05-08
143 / 419
LoanFlexAdjustCollateralResp
42.261. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
collateralCoin
string
false
none
none
currentLTV
number
false
none
none
direction
string
false
none
none
loanCoin
string
false
none
none
LoanFlexBorrowHistoryResp
{ 
  "borrowTime": 0, 
  "collateralCoin": "string", 
  "initialCollateralAmount": 0, 
  "initialLoanAmount": 0, 
  "loanCoin": "string", 
  "status": "string" 
} 
 
LoanFlexBorrowHistoryResp
42.262. Properties
Name
Type
Required
Restrictions
Description
borrowTime
integer(int64)
false
none
borrow time
collateralCoin
string
false
none
collateral coin
initialCollateralAmount
number
false
none
initial collateral amount
initialLoanAmount
number
false
none
initial loan amount
loanCoin
string
false
none
loan coin
status
string
false
none
status
LoanFlexBorrowResp
{ 
  "collateralAmount": 0, 
  "collateralCoin": "string", 
  "loanAmount": 0, 
  "loanCoin": "string", 
  "status": "string" 
} 
 
LoanFlexBorrowResp
42.263. Properties
Name
Type
Required
Restrictions
Description
collateralAmount
number
false
none
none
collateralCoin
string
false
none
none
loanAmount
number
false
none
none
loanCoin
string
false
none
none
status
string
false
none
none
LoanFlexOngoingOrderResp


---

## Page 144

sapi-v7.4.md
2024-05-08
144 / 419
{ 
  "collateralAmount": 0, 
  "collateralCoin": "string", 
  "currentLTV": 0, 
  "loanCoin": "string", 
  "totalDebt": 0 
} 
 
LoanFlexOngoingOrderResp
42.264. Properties
Name
Type
Required
Restrictions
Description
collateralAmount
number
false
none
collateral Amount
collateralCoin
string
false
none
collateral coin
currentLTV
number
false
none
ltv
loanCoin
string
false
none
loan coin
totalDebt
number
false
none
total Debt
LoanFlexRepayHistoryResp
{ 
  "collateralCoin": "string", 
  "collateralReturn": 0, 
  "loanCoin": "string", 
  "repayAmount": 0, 
  "repayStatus": "string", 
  "repayTime": 0 
} 
 
LoanFlexRepayHistoryResp
42.265. Properties
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
collateral coin
collateralReturn
number
false
none
collateral return
loanCoin
string
false
none
loan coin
repayAmount
number
false
none
repay amount
repayStatus
string
false
none
repay status
repayTime
integer(int64)
false
none
repay time
LoanFlexRepayResp
{ 
  "collateralCoin": "string", 
  "currentLTV": 0, 
  "fullRepayment": true, 
  "loanCoin": "string", 
  "remainingCollateral": 0, 
  "remainingDebt": 0, 
  "repayStatus": "string" 
} 
 
LoanFlexRepayResp
42.266. Properties
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
none


---

## Page 145

sapi-v7.4.md
2024-05-08
145 / 419
Name
Type
Required
Restrictions
Description
currentLTV
number
false
none
none
fullRepayment
boolean
false
none
none
loanCoin
string
false
none
none
remainingCollateral
number
false
none
none
remainingDebt
number
false
none
none
repayStatus
string
false
none
none
LoanOtcAccountInfoResp
{ 
  "collateralAccountId": 0, 
  "collateralCoin": "string" 
} 
 
LoanOtcAccountInfoResp
42.267. Properties
Name
Type
Required
Restrictions
Description
collateralAccountId
integer(int64)
false
none
none
collateralCoin
string
false
none
none
LoanOtcBorrowResp
{ 
  "collateralAccountId": "string", 
  "collateralCoin": "string", 
  "loanAccountId": 0, 
  "loanAmount": 0, 
  "loanCoin": "string", 
  "loanTerm": 0, 
  "requestId": 0 
} 
 
LoanOtcBorrowResp
42.268. Properties
Name
Type
Required
Restrictions
Description
collateralAccountId
string
false
none
collateral account
collateralCoin
string
false
none
collateral coin
loanAccountId
integer(int64)
false
none
loan account
loanAmount
number
false
none
loan amount
loanCoin
string
false
none
loan coin
loanTerm
integer(int32)
false
none
loan term
requestId
integer(int64)
false
none
request ID
LoanOtcOngoingOrdersResp
{ 
  "collateralAccountId": "string", 
  "collateralCoin": "string", 
  "collateralValue": 0, 
  "currentLTV": 0, 
  "expirationTime": 0, 
  "initialLtv": "string", 
  "liquidationLtv": "string", 
  "loanCoin": "string", 
  "loanDate": "string", 


---

## Page 146

sapi-v7.4.md
2024-05-08
146 / 419
  "loanRate": "string", 
  "loanTerm": "string", 
  "lockedCollateralValue": 0, 
  "marginCallLtv": "string", 
  "orderId": 0, 
  "residualInterest": 0, 
  "totalCollateralValueAfterHaircut": 0, 
  "totalDebt": 0 
} 
 
LoanOtcOngoingOrdersResp
42.269. Properties
Name
Type
Required
Restrictions
Description
collateralAccountId
string
false
none
collateral account id
collateralCoin
string
false
none
collateral coin
collateralValue
number
false
none
locked collateral value shown in USD value
currentLTV
number
false
none
current ltv
expirationTime
integer(int64)
false
none
expiration time
initialLtv
string
false
none
initial ltv
liquidationLtv
string
false
none
liquidation ltv
loanCoin
string
false
none
loan coin
loanDate
string
false
none
Loan Date
loanRate
string
false
none
Loan Rate
loanTerm
string
false
none
Loan Term
lockedCollateralValue
number
false
none
locked collateral value shown in USD value
marginCallLtv
string
false
none
margin call ltv
orderId
integer(int64)
false
none
order id
residualInterest
number
false
none
residual interest
totalCollateralValueAfterHaircut
number
false
none
total collateral value after haircut shown in USD value
totalDebt
number
false
none
total debt
LoanOtcRenewResp
{ 
  "collateralAccountId": "string", 
  "collateralCoin": "string", 
  "loanAccountId": 0, 
  "loanAmount": 0, 
  "loanCoin": "string", 
  "loanTerm": 0, 
  "yearlyInterestRate": 0 
} 
 
LoanOtcRenewResp
42.270. Properties
Name
Type
Required
Restrictions
Description
collateralAccountId
string
false
none
collateral account
collateralCoin
string
false
none
collateral coin
loanAccountId
integer(int64)
false
none
loan account
loanAmount
number
false
none
loan amount
loanCoin
string
false
none
loan coin
loanTerm
integer(int32)
false
none
loan term


---

## Page 147

sapi-v7.4.md
2024-05-08
147 / 419
Name
Type
Required
Restrictions
Description
yearlyInterestRate
number
false
none
Yearly Interest Rate
LoanOtcRepayHistoryResp
{ 
  "collateralCoin": "string", 
  "loanCoin": "string", 
  "loanDate": 0, 
  "orderId": 0, 
  "repayAmount": 0, 
  "repayStatus": "string", 
  "repayTime": 0 
} 
 
LoanOtcRepayHistoryResp
42.271. Properties
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
collateral coin
loanCoin
string
false
none
loan coin
loanDate
integer(int64)
false
none
借款⽣效时间
orderId
integer(int64)
false
none
order id
repayAmount
number
false
none
repay amount
repayStatus
string
false
none
repay status
repayTime
integer(int64)
false
none
repay time
LoanOtcRepayResp
{ 
  "collateralCoin": "string", 
  "currentLTV": 0, 
  "loanCoin": "string", 
  "remainingInterest": 0, 
  "remainingPrincipal": 0, 
  "repayAmount": 0, 
  "repayStatus": "string" 
} 
 
LoanOtcRepayResp
42.272. Properties
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
collateral coin
currentLTV
number
false
none
current LTV
loanCoin
string
false
none
loan coin
remainingInterest
number
false
none
remaining interest
remainingPrincipal
number
false
none
remaining principal
repayAmount
number
false
none
repay amount
repayStatus
string
false
none
repay status
LoanOtcRequestStatusResp
{ 
  "collateralAccountId": "string", 
  "collateralCoin": "string", 
  "loanAccountId": 0, 
  "loanAmount": 0, 


---

## Page 148

sapi-v7.4.md
2024-05-08
148 / 419
  "loanCoin": "string", 
  "loanDate": 0, 
  "loanTerm": 0, 
  "orderId": 0, 
  "reason": "string", 
  "requestId": 0, 
  "status": "string" 
} 
 
LoanOtcRequestStatusResp
42.273. Properties
Name
Type
Required
Restrictions
Description
collateralAccountId
string
false
none
collateral account
collateralCoin
string
false
none
collateral coin
loanAccountId
integer(int64)
false
none
loan account
loanAmount
number
false
none
loan amount
loanCoin
string
false
none
loan coin
loanDate
integer(int64)
false
none
loan date
loanTerm
integer(int32)
false
none
loan term
orderId
integer(int64)
false
none
order ID
reason
string
false
none
reason
requestId
integer(int64)
false
none
request ID
status
string
false
none
status
LoanRetailAdjustCollateralHistoryResp
{ 
  "adjustTime": 0, 
  "afterLTV": 0, 
  "amount": 0, 
  "collateralCoin": "string", 
  "direction": "string", 
  "loanCoin": "string", 
  "orderId": 0, 
  "preLTV": 0 
} 
 
LoanRetailAdjustCollateralHistoryResp
42.274. Properties
Name
Type
Required
Restrictions
Description
adjustTime
integer(int64)
false
none
none
afterLTV
number
false
none
none
amount
number
false
none
none
collateralCoin
string
false
none
none
direction
string
false
none
none
loanCoin
string
false
none
none
orderId
integer(int64)
false
none
none
preLTV
number
false
none
none
LoanRetailAdjustCollateralResp
{ 
  "amount": 0, 
  "collateralCoin": "string", 
  "currentLTV": 0, 


---

## Page 149

sapi-v7.4.md
2024-05-08
149 / 419
  "direction": "string", 
  "loanCoin": "string" 
} 
 
LoanRetailAdjustCollateralResp
42.275. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
collateralCoin
string
false
none
none
currentLTV
number
false
none
none
direction
string
false
none
none
loanCoin
string
false
none
none
LoanRetailBorrowHistoryResp
{ 
  "borrowTime": 0, 
  "collateralCoin": "string", 
  "hourlyInterestRate": 0, 
  "initialCollateralAmount": 0, 
  "initialLoanAmount": 0, 
  "loanCoin": "string", 
  "loanTerm": 0, 
  "orderId": 0, 
  "status": "string" 
} 
 
LoanRetailBorrowHistoryResp
42.276. Properties
Name
Type
Required
Restrictions
Description
borrowTime
integer(int64)
false
none
borrow time
collateralCoin
string
false
none
collateral coin
hourlyInterestRate
number
false
none
hourly interest rate
initialCollateralAmount
number
false
none
initial collateral amount
initialLoanAmount
number
false
none
initial loan amount
loanCoin
string
false
none
loan coin
loanTerm
integer(int32)
false
none
loan term
orderId
integer(int64)
false
none
order id
status
string
false
none
status
LoanRetailBorrowResp
{ 
  "collateralAmount": 0, 
  "collateralCoin": "string", 
  "hourlyInterestRate": 0, 
  "loanAmount": 0, 
  "loanCoin": "string", 
  "orderId": 0 
} 
 
LoanRetailBorrowResp
42.277. Properties
Name
Type
Required
Restrictions
Description


---

## Page 150

sapi-v7.4.md
2024-05-08
150 / 419
Name
Type
Required
Restrictions
Description
collateralAmount
number
false
none
collateral amount
collateralCoin
string
false
none
loan coin
hourlyInterestRate
number
false
none
hourly interest rate
loanAmount
number
false
none
loan amount
loanCoin
string
false
none
loan coin
orderId
integer(int64)
false
none
orderId
LoanRetailOngoingOrdersResp
{ 
  "collateralAmount": 0, 
  "collateralCoin": "string", 
  "currentLTV": 0, 
  "expirationTime": 0, 
  "loanCoin": "string", 
  "orderId": 0, 
  "residualInterest": 0, 
  "totalDebt": 0 
} 
 
LoanRetailOngoingOrdersResp
42.278. Properties
Name
Type
Required
Restrictions
Description
collateralAmount
number
false
none
initial collateral amount
collateralCoin
string
false
none
collateral coin
currentLTV
number
false
none
current ltv
expirationTime
integer(int64)
false
none
expiration time
loanCoin
string
false
none
loan coin
orderId
integer(int64)
false
none
order id
residualInterest
number
false
none
residual interest
totalDebt
number
false
none
total debt
LoanRetailRepayHistoryResp
{ 
  "collateralCoin": "string", 
  "collateralReturn": 0, 
  "collateralUsed": 0, 
  "loanCoin": "string", 
  "orderId": 0, 
  "repayAmount": 0, 
  "repayStatus": "string", 
  "repayTime": 0, 
  "repayType": 0 
} 
 
LoanRetailRepayHistoryResp
42.279. Properties
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
collateral coin
collateralReturn
number
false
none
collateral return
collateralUsed
number
false
none
collatera used when collateral repay, null for regular repay
loanCoin
string
false
none
loan coin


---

## Page 151

sapi-v7.4.md
2024-05-08
151 / 419
Name
Type
Required
Restrictions
Description
orderId
integer(int64)
false
none
order id
repayAmount
number
false
none
repay amount
repayStatus
string
false
none
repay status
repayTime
integer(int64)
false
none
repay time
repayType
integer(int32)
false
none
repay type
LoanRetailRepayResp
{ 
  "collateralCoin": "string", 
  "currentLTV": 0, 
  "loanCoin": "string", 
  "remainingCollateral": 0, 
  "remainingInterest": 0, 
  "remainingPrincipal": 0, 
  "repayStatus": "string" 
} 
 
LoanRetailRepayResp
42.280. Properties
Name
Type
Required
Restrictions
Description
collateralCoin
string
false
none
none
currentLTV
number
false
none
none
loanCoin
string
false
none
none
remainingCollateral
number
false
none
none
remainingInterest
number
false
none
none
remainingPrincipal
number
false
none
none
repayStatus
string
false
none
none
LoanableAssetsDataForSapiResp
{ 
  "_14dDailyInterestRate": 0, 
  "_14dHourlyInterestRate": 0, 
  "_180dDailyInterestRate": 0, 
  "_180dHourlyInterestRate": 0, 
  "_30dDailyInterestRate": 0, 
  "_30dHourlyInterestRate": 0, 
  "_7dDailyInterestRate": 0, 
  "_7dHourlyInterestRate": 0, 
  "_90dDailyInterestRate": 0, 
  "_90dHourlyInterestRate": 0, 
  "loanCoin": "string", 
  "maxLimit": 0, 
  "minLimit": 0, 
  "vipLevel": 0 
} 
 
LoanableAssetsDataForSapiResp
42.281. Properties
Name
Type
Required
Restrictions
Description
_14dDailyInterestRate
number
false
none
none
_14dHourlyInterestRate
number
false
none
none
_180dDailyInterestRate
number
false
none
none
_180dHourlyInterestRate
number
false
none
none


---

## Page 152

sapi-v7.4.md
2024-05-08
152 / 419
Name
Type
Required
Restrictions
Description
_30dDailyInterestRate
number
false
none
none
_30dHourlyInterestRate
number
false
none
none
_7dDailyInterestRate
number
false
none
none
_7dHourlyInterestRate
number
false
none
none
_90dDailyInterestRate
number
false
none
none
_90dHourlyInterestRate
number
false
none
none
loanCoin
string
false
none
none
maxLimit
number
false
none
none
minLimit
number
false
none
none
vipLevel
integer(int32)
false
none
none
MMCollectionInfoVo
{ 
  "floorPrice": 0, 
  "lastTrading": 0, 
  "totalItems": 0, 
  "tradingVolumn": 0 
} 
 
MMCollectionInfoVo
42.282. Properties
Name
Type
Required
Restrictions
Description
floorPrice
number
false
none
none
lastTrading
number
false
none
none
totalItems
integer(int32)
false
none
none
tradingVolumn
number
false
none
none
MMQueryProductItem
{ 
  "brandingId": 0, 
  "brandingName": "string", 
  "buyoutPrice": 0, 
  "collectionId": 0, 
  "collectionName": "string", 
  "contractAddress": "string", 
  "creator": "string", 
  "currency": "string", 
  "expireDate": "2019-08-24T14:15:22Z", 
  "itemId": 0, 
  "itemName": "string", 
  "network": "string", 
  "nftType": 0, 
  "orderType": 0, 
  "owner": "string", 
  "productId": 0, 
  "rarity": 0, 
  "startingPrice": 0, 
  "title": "string", 
  "tokenId": "string" 
} 
 
MMQueryProductItem
42.283. Properties
Name
Type
Required
Restrictions
Description


---

## Page 153

sapi-v7.4.md
2024-05-08
153 / 419
Name
Type
Required
Restrictions
Description
brandingId
integer(int64)
false
none
none
brandingName
string
false
none
none
buyoutPrice
number
false
none
none
collectionId
integer(int64)
false
none
none
collectionName
string
false
none
none
contractAddress
string
false
none
none
creator
string
false
none
none
currency
string
false
none
none
expireDate
string(date-time)
false
none
none
itemId
integer(int64)
false
none
none
itemName
string
false
none
none
network
string
false
none
none
nftType
integer(int32)
false
none
none
orderType
integer(int32)
false
none
none
owner
string
false
none
none
productId
integer(int64)
false
none
none
rarity
integer(int32)
false
none
none
startingPrice
number
false
none
none
title
string
false
none
none
tokenId
string
false
none
none
MakeOrderReq
{ 
  "advOrderNumber": "string", 
  "asset": "string", 
  "buyType": "BY_AMOUNT", 
  "fiatUnit": "string", 
  "matchPrice": 0, 
  "origin": "string", 
  "payId": 0, 
  "payType": "string", 
  "totalAmount": 0, 
  "tradeType": "BUY" 
} 
 
MakeOrderReq
42.284. Properties
Name
Type
Required
Restrictions
Description
advOrderNumber
string
false
none
Adv order number for the placed ad
asset
string
false
none
Cryptocurrency asset: BTC
buyType
string
false
none
Price buy type: (BY_MONEY, BY_AMOUNT)
fiatUnit
string
false
none
Fiat currency: CNY
matchPrice
number
false
none
Order match price
origin
string
false
none
Source of order match
payId
integer(int64)
false
none
User payment method id for sell order
payType
string
false
none
Payment method, e.g.: BANK, WECHAT
totalAmount
number
false
none
Purchase total amount in fiat currency
tradeType
string
false
none
Order trade type. 0: BUY, 1: SELL
42.284.1. Enumerated Values


---

## Page 154

sapi-v7.4.md
2024-05-08
154 / 419
Property
Value
buyType
BY_AMOUNT
buyType
BY_MONEY
tradeType
BUY
tradeType
SELL
MakeOrderResp
{ 
  "orderMatch": { 
    "additionalKycVerify": 0, 
    "address": "string", 
    "advMainUserId": 0, 
    "advMakerRoles": "string", 
    "advOrderId": 0, 
    "advOrderNumber": "string", 
    "advUserId": 0, 
    "allowComplainTime": "2019-08-24T14:15:22Z", 
    "amount": 0, 
    "asset": "string", 
    "assetTicketSize": "string", 
    "buyerCompanyAccountName": "string", 
    "buyerCreditScore": 0, 
    "buyerMobilePhone": "string", 
    "buyerName": "string", 
    "buyerNickname": "string", 
    "canCancelComplaintOrder": true, 
    "cancelComplaintTime": "2019-08-24T14:15:22Z", 
    "cancelReasonAdditional": "string", 
    "cancelReasonDesc": "string", 
    "cancelTime": "2019-08-24T14:15:22Z", 
    "chatUnreadCount": 0, 
    "classify": "string", 
    "clientType": "string", 
    "commission": 0, 
    "commissionRate": 0, 
    "complainFreezeTime": "2019-08-24T14:15:22Z", 
    "complaintDeadline": "2019-08-24T14:15:22Z", 
    "complaintReason": "string", 
    "complaintStatus": 0, 
    "confirmPaidType": "string", 
    "confirmPayEndTime": "2019-08-24T14:15:22Z", 
    "confirmPayTime": "2019-08-24T14:15:22Z", 
    "confirmPayTimeout": 0, 
    "confirmPayedExpireMinute": 0, 
    "createTime": "2019-08-24T14:15:22Z", 
    "currencyRate": 0, 
    "currencyTicketSize": "string", 
    "fiatSymbol": "string", 
    "fiatUnit": "string", 
    "idNumber": "string", 
    "isBuyerCompanyAccount": true, 
    "isChatEnabled": true, 
    "isComplaintAllowed": true, 
    "isRiskCount": 0, 
    "isSellerCompanyAccount": true, 
    "isSupportVirtualNum": true, 
    "lengthOfConfirmTime": 0, 
    "lengthOfPayTime": 0, 
    "mainUserId": 0, 
    "maker": { 
      "advConfirmTime": 0, 
      "badges": [ 
        "string" 
      ], 
      "businessMobile": "string", 
      "businessStatus": 0, 
      "complaintCount": 0, 
      "countyCode": "string", 
      "createTime": "2019-08-24T14:15:22Z", 
      "email": "string", 
      "eqMargin": 0, 
      "eqMarginUnit": "string", 
      "fiatTradingAccount": 0, 
      "firstOrderDays": 0, 
      "fundpwdStatus": 0, 


---

## Page 155

sapi-v7.4.md
2024-05-08
155 / 419
      "id": 0, 
      "informMethods": "string", 
      "maliceInitiatorCount": 0, 
      "margin": 0, 
      "marginAsset": { 
        "asset": "string", 
        "createTime": "2019-08-24T14:15:22Z", 
        "decimalScale": 0, 
        "iconUrl": "string", 
        "isEnable": 0, 
        "isTransVisible": 0, 
        "name": "string", 
        "ranking": 0, 
        "updateTime": "2019-08-24T14:15:22Z" 
      }, 
      "marginFreeze": 0, 
      "marginStatsItems": [ 
        { 
          "margin": 0, 
          "marginUnit": "string" 
        } 
      ], 
      "marginUnit": "string", 
      "maskedBusinessMobile": "string", 
      "maskedEmail": "string", 
      "merchantType": "string", 
      "mobile": "string", 
      "mobileDisplayStatus": 0, 
      "monthFinishRate": 0, 
      "monthOrderCount": 0, 
      "nickColor": "string", 
      "nickName": "string", 
      "onlineStatus": 0, 
      "orderCount": 0, 
      "overComplained": 0, 
      "parentId": 0, 
      "payMethodCount": 0, 
      "proMerchantVo": { 
        "merchantDescription": "string", 
        "merchantLogo": "string" 
      }, 
      "realName": "string", 
      "registerDays": 0, 
      "registrationTime": "2019-08-24T14:15:22Z", 
      "tradingAccount": 0, 
      "updateTime": "2019-08-24T14:15:22Z", 
      "userGradeInstanceVo": { 
        "agreementSigned": 0, 
        "authorityId": 0, 
        "createTime": "2019-08-24T14:15:22Z", 
        "emailStatus": 0, 
        "id": 0, 
        "kycStatus": 0, 
        "marginStatus": 0, 
        "mobileStatus": 0, 
        "nickNameStatus": 0, 
        "parentId": 0, 
        "qualificationId": 0, 
        "updateTime": "2019-08-24T14:15:22Z", 
        "userGradeQualificationVo": { 
          "accountGrade": null, 
          "accountType": null, 
          "agreement": null, 
          "countryCode": null, 
          "createTime": null, 
          "defaultAuthority": null, 
          "email": null, 
          "gradeName": null, 
          "id": null, 
          "kycVerify": null, 
          "margin": null, 
          "mobile": null, 
          "nickName": null, 
          "typeName": null, 
          "updateTime": null 
        }, 
        "userId": 0 
      }, 
      "userId": 0, 
      "userKycVo": { 
        "address": "string", 


---

## Page 156

sapi-v7.4.md
2024-05-08
156 / 419
        "addressStatus": "string", 
        "basicStatus": "string", 
        "certificateStatus": 0, 
        "companyName": "string", 
        "countyCode": "string", 
        "createTime": "2019-08-24T14:15:22Z", 
        "faceStatus": "string", 
        "firstName": "string", 
        "idNo": "string", 
        "identityStatus": "string", 
        "kycLevel": 0, 
        "kycStatus": "string", 
        "kycType": "string", 
        "lastName": "string", 
        "middleName": "string", 
        "updateTime": "2019-08-24T14:15:22Z", 
        "userId": 0 
      }, 
      "userNo": "string", 
      "userOrderHistoryStatsVo": { 
        "accountAge": 0, 
        "appealedOrderCountHistorical": 0, 
        "appealedOrderCountLast30Days": 0, 
        "appealedRateHistorical": 0, 
        "appealedRateLast30Days": 0, 
        "avgPayTime": 0, 
        "avgPayTimeOfLatest30day": 0, 
        "avgReleaseTime": 0, 
        "avgReleaseTimeOfLatest30day": 0, 
        "buyOrderNum": 0, 
        "buyOrderNumOfLatest30day": 0, 
        "canceledBuyOrderNum": 0, 
        "canceledBuyOrderNumOfLatest30day": 0, 
        "completedBuyOrderNum": 0, 
        "completedBuyOrderNumOfLatest30day": 0, 
        "completedBuyOrderTotalBtcAmount": 0, 
        "completedBuyOrderTotalBtcAmountOfLatest30day": 0, 
        "completedOrderNum": 0, 
        "completedOrderNumOfLatest30day": 0, 
        "completedOrderTotalBtcAmount": 0, 
        "completedOrderTotalBtcAmountOfLatest30day": 0, 
        "completedSellOrderNum": 0, 
        "completedSellOrderNumOfLatest30day": 0, 
        "completedSellOrderTotalBtcAmount": 0, 
        "completedSellOrderTotalBtcAmountOfLatest30day": 0, 
        "counterpartyNum": 0, 
        "creditScore": 0, 
        "finishRate": 0, 
        "finishRateLatest30Day": 0 
      }, 
      "userOrderInProgressStatsVo": { 
        "buyerPayedCount": 0, 
        "inAppealCount": 0, 
        "inAppealCountAfterBuyerPaid": 0, 
        "inAppealCountAfterCancelled": 0, 
        "inAppealCountAfterCancelledBySystem": 0, 
        "inAppealCountAfterCompleted": 0, 
        "inProcessCount": 0, 
        "tradingCount": 0, 
        "userId": 0 
      }, 
      "userType": "string" 
    }, 
    "merchantNo": "string", 
    "nickColor": "string", 
    "notifyPayEndTime": "2019-08-24T14:15:22Z", 
    "notifyPayTime": "2019-08-24T14:15:22Z", 
    "notifyPayedExpireMinute": 0, 
    "onlineStatus": "string", 
    "orderComplaintAmount": { 
      "complaintAmount": 0, 
      "completedComplaintAmount": 0, 
      "processingComplaintAmount": 0 
    }, 
    "orderNumber": "string", 
    "orderStatus": 0, 
    "orderTakerRoles": "string", 
    "origin": "string", 
    "payAccount": "string", 
    "payBank": "string", 
    "payMethods": [ 


---

## Page 157

sapi-v7.4.md
2024-05-08
157 / 419
      { 
        "advCount": 0, 
        "createTime": "2019-08-24T14:15:22Z", 
        "currentPayAmount": 0, 
        "fieldList": [ 
          { 
            "createTime": null, 
            "errorKey": null, 
            "errorWord": null, 
            "fieldContentType": null, 
            "fieldId": null, 
            "fieldName": null, 
            "fieldTitle": null, 
            "fieldTitleKey": null, 
            "fieldValue": null, 
            "hintKey": null, 
            "hintWord": null, 
            "id": null, 
            "isCopyable": null, 
            "isDisplay": null, 
            "isEncrypt": null, 
            "isRequired": null, 
            "lengthLimit": null, 
            "restrictionType": null, 
            "sequence": null, 
            "status": null, 
            "updateTime": null 
          } 
        ], 
        "iconUrlColor": "string", 
        "id": 0, 
        "isRemoved": 0, 
        "mainUserId": 0, 
        "online": true, 
        "payLimit": 0, 
        "payLimitUnit": "string", 
        "payStatus": "ACTIVE", 
        "tradeMethodBgColor": "string", 
        "tradeMethodIdentifier": "string", 
        "tradeMethodName": "string", 
        "tradeMethodRisk": "string", 
        "tradeMethodShortName": "string", 
        "updateTime": "2019-08-24T14:15:22Z", 
        "userId": 0 
      } 
    ], 
    "paySubBank": "string", 
    "payTimeLimit": 0, 
    "payType": "string", 
    "payTypeDesc": "string", 
    "payee": "string", 
    "price": 0, 
    "priceTicketSize": "string", 
    "publisherType": "string", 
    "qrCodePath": "string", 
    "quickConfirmAmountUpLimit": 0, 
    "remark": "string", 
    "selectedPayId": 0, 
    "sellerCompanyAccountName": "string", 
    "sellerCreditScore": 0, 
    "sellerMobilePhone": "string", 
    "sellerName": "string", 
    "sellerNickname": "string", 
    "statFlag": 0, 
    "store": { 
      "applyStatus": 0, 
      "availableMargin": 0, 
      "countryCode": "string", 
      "distance": 0, 
      "enable": "string", 
      "fineAmount": 0, 
      "friOpenTime": "string", 
      "friOpenTimeLocal": "string", 
      "fullAddress": "string", 
      "geoCode": "string", 
      "latitude": 0, 
      "longitude": 0, 
      "margin": 0, 
      "marginFreeze": 0, 
      "marginUnit": "string", 
      "monOpenTime": "string", 


---

## Page 158

sapi-v7.4.md
2024-05-08
158 / 419
      "monOpenTimeLocal": "string", 
      "processingAmount": 0, 
      "refundProcessingAmount": 0, 
      "refundableFineAmount": 0, 
      "remark": "string", 
      "satOpenTime": "string", 
      "satOpenTimeLocal": "string", 
      "status": 0, 
      "storeAddressVo": { 
        "building": "string", 
        "city": "string", 
        "country": "string", 
        "flat": "string", 
        "floor": "string", 
        "province": "string", 
        "remark": "string", 
        "street": "string", 
        "zipCode": "string" 
      }, 
      "storeId": 0, 
      "storeMaterialItemVoList": [ 
        { 
          "dataFrom": "string", 
          "dataType": "string", 
          "fileType": "string", 
          "id": 0, 
          "itemData": "string", 
          "itemIdentifier": "string", 
          "storeId": 0 
        } 
      ], 
      "storeName": "string", 
      "storeShortName": "string", 
      "submissionTime": "2019-08-24T14:15:22Z", 
      "sunOpenTime": "string", 
      "sunOpenTimeLocal": "string", 
      "thuOpenTime": "string", 
      "thuOpenTimeLocal": "string", 
      "timeZone": "string", 
      "tueOpenTime": "string", 
      "tueOpenTimeLocal": "string", 
      "updateTime": "2019-08-24T14:15:22Z", 
      "userId": 0, 
      "valid": true, 
      "wedOpenTime": "string", 
      "wedOpenTimeLocal": "string" 
    }, 
    "sysCancelTime": "2019-08-24T14:15:22Z", 
    "taker": { 
      "advConfirmTime": 0, 
      "badges": [ 
        "string" 
      ], 
      "businessMobile": "string", 
      "businessStatus": 0, 
      "complaintCount": 0, 
      "countyCode": "string", 
      "createTime": "2019-08-24T14:15:22Z", 
      "email": "string", 
      "eqMargin": 0, 
      "eqMarginUnit": "string", 
      "fiatTradingAccount": 0, 
      "firstOrderDays": 0, 
      "fundpwdStatus": 0, 
      "id": 0, 
      "informMethods": "string", 
      "maliceInitiatorCount": 0, 
      "margin": 0, 
      "marginAsset": { 
        "asset": "string", 
        "createTime": "2019-08-24T14:15:22Z", 
        "decimalScale": 0, 
        "iconUrl": "string", 
        "isEnable": 0, 
        "isTransVisible": 0, 
        "name": "string", 
        "ranking": 0, 
        "updateTime": "2019-08-24T14:15:22Z" 
      }, 
      "marginFreeze": 0, 
      "marginStatsItems": [ 


---

## Page 159

sapi-v7.4.md
2024-05-08
159 / 419
        { 
          "margin": 0, 
          "marginUnit": "string" 
        } 
      ], 
      "marginUnit": "string", 
      "maskedBusinessMobile": "string", 
      "maskedEmail": "string", 
      "merchantType": "string", 
      "mobile": "string", 
      "mobileDisplayStatus": 0, 
      "monthFinishRate": 0, 
      "monthOrderCount": 0, 
      "nickColor": "string", 
      "nickName": "string", 
      "onlineStatus": 0, 
      "orderCount": 0, 
      "overComplained": 0, 
      "parentId": 0, 
      "payMethodCount": 0, 
      "proMerchantVo": { 
        "merchantDescription": "string", 
        "merchantLogo": "string" 
      }, 
      "realName": "string", 
      "registerDays": 0, 
      "registrationTime": "2019-08-24T14:15:22Z", 
      "tradingAccount": 0, 
      "updateTime": "2019-08-24T14:15:22Z", 
      "userGradeInstanceVo": { 
        "agreementSigned": 0, 
        "authorityId": 0, 
        "createTime": "2019-08-24T14:15:22Z", 
        "emailStatus": 0, 
        "id": 0, 
        "kycStatus": 0, 
        "marginStatus": 0, 
        "mobileStatus": 0, 
        "nickNameStatus": 0, 
        "parentId": 0, 
        "qualificationId": 0, 
        "updateTime": "2019-08-24T14:15:22Z", 
        "userGradeQualificationVo": { 
          "accountGrade": null, 
          "accountType": null, 
          "agreement": null, 
          "countryCode": null, 
          "createTime": null, 
          "defaultAuthority": null, 
          "email": null, 
          "gradeName": null, 
          "id": null, 
          "kycVerify": null, 
          "margin": null, 
          "mobile": null, 
          "nickName": null, 
          "typeName": null, 
          "updateTime": null 
        }, 
        "userId": 0 
      }, 
      "userId": 0, 
      "userKycVo": { 
        "address": "string", 
        "addressStatus": "string", 
        "basicStatus": "string", 
        "certificateStatus": 0, 
        "companyName": "string", 
        "countyCode": "string", 
        "createTime": "2019-08-24T14:15:22Z", 
        "faceStatus": "string", 
        "firstName": "string", 
        "idNo": "string", 
        "identityStatus": "string", 
        "kycLevel": 0, 
        "kycStatus": "string", 
        "kycType": "string", 
        "lastName": "string", 
        "middleName": "string", 
        "updateTime": "2019-08-24T14:15:22Z", 
        "userId": 0 


---

## Page 160

sapi-v7.4.md
2024-05-08
160 / 419
      }, 
      "userNo": "string", 
      "userOrderHistoryStatsVo": { 
        "accountAge": 0, 
        "appealedOrderCountHistorical": 0, 
        "appealedOrderCountLast30Days": 0, 
        "appealedRateHistorical": 0, 
        "appealedRateLast30Days": 0, 
        "avgPayTime": 0, 
        "avgPayTimeOfLatest30day": 0, 
        "avgReleaseTime": 0, 
        "avgReleaseTimeOfLatest30day": 0, 
        "buyOrderNum": 0, 
        "buyOrderNumOfLatest30day": 0, 
        "canceledBuyOrderNum": 0, 
        "canceledBuyOrderNumOfLatest30day": 0, 
        "completedBuyOrderNum": 0, 
        "completedBuyOrderNumOfLatest30day": 0, 
        "completedBuyOrderTotalBtcAmount": 0, 
        "completedBuyOrderTotalBtcAmountOfLatest30day": 0, 
        "completedOrderNum": 0, 
        "completedOrderNumOfLatest30day": 0, 
        "completedOrderTotalBtcAmount": 0, 
        "completedOrderTotalBtcAmountOfLatest30day": 0, 
        "completedSellOrderNum": 0, 
        "completedSellOrderNumOfLatest30day": 0, 
        "completedSellOrderTotalBtcAmount": 0, 
        "completedSellOrderTotalBtcAmountOfLatest30day": 0, 
        "counterpartyNum": 0, 
        "creditScore": 0, 
        "finishRate": 0, 
        "finishRateLatest30Day": 0 
      }, 
      "userOrderInProgressStatsVo": { 
        "buyerPayedCount": 0, 
        "inAppealCount": 0, 
        "inAppealCountAfterBuyerPaid": 0, 
        "inAppealCountAfterCancelled": 0, 
        "inAppealCountAfterCancelledBySystem": 0, 
        "inAppealCountAfterCompleted": 0, 
        "inProcessCount": 0, 
        "tradingCount": 0, 
        "userId": 0 
      }, 
      "userType": "string" 
    }, 
    "takerAmount": 0, 
    "takerCommission": 0, 
    "takerCommissionRate": 0, 
    "totalPrice": 0, 
    "tradeMethodCommissionRateVoList": [ 
      { 
        "commissionRate": 0, 
        "tradeMethodIdentifier": "string", 
        "tradeMethodName": "string" 
      } 
    ], 
    "tradeType": "BUY", 
    "unreadCount": 0, 
    "updateTime": "2019-08-24T14:15:22Z", 
    "userId": 0 
  }, 
  "result": true 
} 
 
MakeOrderResp
42.285. Properties
Name
Type
Required
Restrictions
Description
orderMatch
OrderMatchResp
false
none
none
result
boolean
false
none
none
ManagerSubDepositAddressResp


---

## Page 161

sapi-v7.4.md
2024-05-08
161 / 419
{ 
  "address": "string", 
  "coin": "string", 
  "networkSet": [ 
    "string" 
  ], 
  "tag": "string", 
  "url": "string" 
} 
 
ManagerSubDepositAddressResp
42.286. Properties
Name
Type
Required
Restrictions
Description
address
string
false
none
none
coin
string
false
none
none
networkSet
[string]
false
none
none
tag
string
false
none
none
url
string
false
none
none
ManagerSubTransferHistoryResp
{ 
  "count": 0, 
  "managerSubTransferHistoryVos": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "createTime": "2019-08-24T14:15:22Z", 
      "fromAccountType": "string", 
      "fromEmail": "string", 
      "scheduledData": 0, 
      "status": "string", 
      "toAccountType": "string", 
      "toEmail": "string", 
      "tranId": 0 
    } 
  ] 
} 
 
ManagerSubTransferHistoryResp
42.287. Properties
Name
Type
Required
Restrictions
Description
count
integer(int64)
false
none
记录数
managerSubTransferHistoryVos
[ManagerSubTransferHistoryVo]
false
none
划转数据
ManagerSubTransferHistoryVo
{ 
  "amount": 0, 
  "asset": "string", 
  "createTime": "2019-08-24T14:15:22Z", 
  "fromAccountType": "string", 
  "fromEmail": "string", 
  "scheduledData": 0, 
  "status": "string", 
  "toAccountType": "string", 
  "toEmail": "string", 
  "tranId": 0 
} 
 
ManagerSubTransferHistoryVo


---

## Page 162

sapi-v7.4.md
2024-05-08
162 / 419
42.288. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
createTime
string(date-time)
false
none
none
fromAccountType
string
false
none
none
fromEmail
string
false
none
none
scheduledData
integer(int64)
false
none
none
status
string
false
none
none
toAccountType
string
false
none
none
toEmail
string
false
none
none
tranId
integer(int64)
false
none
none
ManagerSubUserAccountResp
{ 
  "code": 0, 
  "msg": "string", 
  "snapshotVos": [ 
    { 
      "data": {}, 
      "type": "string", 
      "updateTime": 0 
    } 
  ] 
} 
 
ManagerSubUserAccountResp
42.289. Properties
Name
Type
Required
Restrictions
Description
code
integer(int32)
false
none
none
msg
string
false
none
none
snapshotVos
[QueryAssetByTypeVo]
false
none
none
ManagerSubUserAssetDetail
{ 
  "availableBalance": 0, 
  "btcValue": 0, 
  "coin": "string", 
  "inOrder": 0, 
  "name": "string", 
  "totalBalance": 0 
} 
 
ManagerSubUserAssetDetail
42.290. Properties
Name
Type
Required
Restrictions
Description
availableBalance
number
false
none
可⽤资产
btcValue
number
false
none
折合BTC
coin
string
false
none
币种简称
inOrder
number
false
none
锁定资产
name
string
false
none
币种全名


---

## Page 163

sapi-v7.4.md
2024-05-08
163 / 419
Name
Type
Required
Restrictions
Description
totalBalance
number
false
none
总资产
ManagerSubUserInfoVo
{ 
  "bindParentEmail": "string", 
  "bindParentUserId": 0, 
  "email": "string", 
  "insertTimeStamp": 0, 
  "isFutureEnabled": true, 
  "isMarginEnabled": true, 
  "isSignedLVTRiskAgreement": true, 
  "isSubUserEnabled": true, 
  "isUserActive": true, 
  "managersubUserId": 0, 
  "remark": "string", 
  "rootUserId": 0 
} 
 
ManagerSubUserInfoVo
42.291. Properties
Name
Type
Required
Restrictions
Description
bindParentEmail
string
false
none
none
bindParentUserId
integer(int64)
false
none
none
email
string
false
none
none
insertTimeStamp
integer(int64)
false
none
none
isFutureEnabled
boolean
false
none
是否启⽤future
isMarginEnabled
boolean
false
none
是否启⽤margin
isSignedLVTRiskAgreement
boolean
false
none
是否签署leverage token⻛险协议
isSubUserEnabled
boolean
false
none
是否启⽤⼦账户
isUserActive
boolean
false
none
是否激活
managersubUserId
integer(int64)
false
none
none
remark
string
false
none
none
rootUserId
integer(int64)
false
none
none
ManagerSubUserMarginAssetResp
{ 
  "marginLevel": 0, 
  "totalAssetOfBtc": 0, 
  "totalLiabilityOfBtc": 0, 
  "totalNetAssetOfBtc": 0, 
  "userAssets": [ 
    { 
      "asset": "string", 
      "borrowed": 0, 
      "free": 0, 
      "interest": 0, 
      "locked": 0, 
      "netAsset": 0 
    } 
  ] 
} 
 
ManagerSubUserMarginAssetResp
42.292. Properties
Name
Type
Required
Restrictions
Description


---

## Page 164

sapi-v7.4.md
2024-05-08
164 / 419
Name
Type
Required
Restrictions
Description
marginLevel
number
false
none
none
totalAssetOfBtc
number
false
none
none
totalLiabilityOfBtc
number
false
none
none
totalNetAssetOfBtc
number
false
none
none
userAssets
[MarginUserAsset]
false
none
none
ManagerSubUserTransferResp
{ 
  "tranId": 0 
} 
 
ManagerSubUserTransferResp
42.293. Properties
Name
Type
Required
Restrictions
Description
tranId
integer(int64)
false
none
划转单号
MarginAccountSummaryInfoVoSapiVersion
{ 
  "email": "string", 
  "totalAssetOfBtc": "string", 
  "totalLiabilityOfBtc": "string", 
  "totalNetAssetOfBtc": "string" 
} 
 
MarginAccountSummaryInfoVoSapiVersion
42.294. Properties
Name
Type
Required
Restrictions
Description
email
string
false
none
none
totalAssetOfBtc
string
false
none
⼦账户总资产（单位：BTC
totalLiabilityOfBtc
string
false
none
⼦账户总负债（单位：BTC
totalNetAssetOfBtc
string
false
none
⼦账户净资产（单位：BTC
MarginAssetResp
{ 
  "assetFullName": "string", 
  "assetName": "string", 
  "delistTime": 0, 
  "interestRate": 0, 
  "isBorrowable": true, 
  "isMortgageable": true, 
  "userMinBorrow": 0, 
  "userMinRepay": 0 
} 
 
MarginAssetResp
42.295. Properties
Name
Type
Required
Restrictions
Description
assetFullName
string
false
none
none
assetName
string
false
none
none


---

## Page 165

sapi-v7.4.md
2024-05-08
165 / 419
Name
Type
Required
Restrictions
Description
delistTime
integer(int64)
false
none
none
interestRate
number
false
none
none
isBorrowable
boolean
false
none
none
isMortgageable
boolean
false
none
none
userMinBorrow
number
false
none
none
userMinRepay
number
false
none
none
MarginCapitalFlowResponse
{ 
  "amount": 0, 
  "asset": "string", 
  "id": 0, 
  "symbol": "string", 
  "timestamp": 0, 
  "tranId": 0, 
  "type": "string" 
} 
 
MarginCapitalFlowResponse
42.296. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
⾦额
asset
string
false
none
资产名称
id
integer(int64)
false
none
id
symbol
string
false
none
交易对
timestamp
integer(int64)
false
none
发⽣时间
tranId
integer(int64)
false
none
流⽔id
type
string
false
none
流⽔类型
MarginCollateralRatio
{ 
  "discountRate": 0, 
  "maxUsdValue": 0, 
  "minUsdValue": 0 
} 
 
MarginCollateralRatio
42.297. Properties
Name
Type
Required
Restrictions
Description
discountRate
number
false
none
none
maxUsdValue
number
false
none
none
minUsdValue
number
false
none
none
MarginCollateralRatioResp
{ 
  "assetNames": [ 
    "string" 
  ], 
  "collaterals": [ 
    { 
      "discountRate": 0, 


---

## Page 166

sapi-v7.4.md
2024-05-08
166 / 419
      "maxUsdValue": 0, 
      "minUsdValue": 0 
    } 
  ] 
} 
 
MarginCollateralRatioResp
42.298. Properties
Name
Type
Required
Restrictions
Description
assetNames
[string]
false
none
none
collaterals
[MarginCollateralRatio]
false
none
none
MarginDelistScheduleResp
{ 
  "crossMarginAssets": [ 
    "string" 
  ], 
  "delistTime": 0, 
  "isolatedMarginSymbols": [ 
    "string" 
  ] 
} 
 
MarginDelistScheduleResp
42.299. Properties
Name
Type
Required
Restrictions
Description
crossMarginAssets
[string]
false
none
none
delistTime
integer(int64)
false
none
none
isolatedMarginSymbols
[string]
false
none
none
MarginDownloadConfigResponse
{ 
  "downloadUrl": "string", 
  "generationTime": 0, 
  "status": "string" 
} 
 
MarginDownloadConfigResponse
42.300. Properties
Name
Type
Required
Restrictions
Description
downloadUrl
string
false
none
none
generationTime
integer(int64)
false
none
none
status
string
false
none
none
MarginFeeResponse
{ 
  "borrowLimit": 0, 
  "borrowable": true, 
  "coin": "string", 
  "dailyInterest": 0, 
  "marginablePairs": [ 
    "string" 
  ], 
  "transferIn": true, 


---

## Page 167

sapi-v7.4.md
2024-05-08
167 / 419
  "vipLevel": 0, 
  "yearlyInterest": 0 
} 
 
MarginFeeResponse
42.301. Properties
Name
Type
Required
Restrictions
Description
borrowLimit
number
false
none
最⼤可借
borrowable
boolean
false
none
是否可借
coin
string
false
none
币种名称
dailyInterest
number
false
none
⽇利率
marginablePairs
[string]
false
none
⽀持币对
transferIn
boolean
false
none
是否可转⼊
vipLevel
integer(int32)
false
none
vip等级
yearlyInterest
number
false
none
年利率
MarginLeverageBracketResp
{ 
  "assetNames": [ 
    "string" 
  ], 
  "brackets": [ 
    { 
      "fastNum": 0, 
      "initialMarginRate": 0, 
      "leverage": 0, 
      "maintenanceMarginRate": 0, 
      "maxDebt": 0 
    } 
  ], 
  "rank": 0 
} 
 
MarginLeverageBracketResp
42.302. Properties
Name
Type
Required
Restrictions
Description
assetNames
[string]
false
none
none
brackets
[LeverageBracket]
false
none
none
rank
integer(int32)
false
none
none
MarginPairResp
{ 
  "base": "string", 
  "id": 0, 
  "isBuyAllowed": true, 
  "isMarginTrade": true, 
  "isSellAllowed": true, 
  "quote": "string", 
  "symbol": "string" 
} 
 
MarginPairResp
42.303. Properties
Name
Type
Required
Restrictions
Description


---

## Page 168

sapi-v7.4.md
2024-05-08
168 / 419
Name
Type
Required
Restrictions
Description
base
string
false
none
none
id
integer(int64)
false
none
none
isBuyAllowed
boolean
false
none
none
isMarginTrade
boolean
false
none
none
isSellAllowed
boolean
false
none
none
quote
string
false
none
none
symbol
string
false
none
none
MarginTierResponse
{ 
  "baseAssetMaxBorrowable": 0, 
  "effectiveMultiple": 0, 
  "initialRiskRatio": 0, 
  "liquidationRiskRatio": 0, 
  "quoteAssetMaxBorrowable": 0, 
  "symbol": "string", 
  "tier": 0 
} 
 
MarginTierResponse
42.304. Properties
Name
Type
Required
Restrictions
Description
baseAssetMaxBorrowable
number
false
none
none
effectiveMultiple
number
false
none
none
initialRiskRatio
number
false
none
none
liquidationRiskRatio
number
false
none
none
quoteAssetMaxBorrowable
number
false
none
none
symbol
string
false
none
none
tier
integer(int32)
false
none
none
MarginTradeCoeffResp
{ 
  "forceLiquidationBar": 0, 
  "marginCallBar": 0, 
  "normalBar": 0 
} 
 
MarginTradeCoeffResp
42.305. Properties
Name
Type
Required
Restrictions
Description
forceLiquidationBar
number
false
none
none
marginCallBar
number
false
none
none
normalBar
number
false
none
none
MarginTradeCoeffVoSapiVersion
{ 
  "canTrade": true, 
  "forceLiquidationBar": 0, 
  "marginCallBar": 0, 
  "normalBar": 0 


---

## Page 169

sapi-v7.4.md
2024-05-08
169 / 419
} 
 
MarginTradeCoeffVoSapiVersion
42.306. Properties
Name
Type
Required
Restrictions
Description
canTrade
boolean
false
none
none
forceLiquidationBar
number
false
none
none
marginCallBar
number
false
none
none
normalBar
number
false
none
none
MarginUserAsset
{ 
  "asset": "string", 
  "borrowed": 0, 
  "free": 0, 
  "interest": 0, 
  "locked": 0, 
  "netAsset": 0 
} 
 
MarginUserAsset
42.307. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
borrowed
number
false
none
none
free
number
false
none
none
interest
number
false
none
none
locked
number
false
none
none
netAsset
number
false
none
none
MarginUserAssetVoSapiVersion
{ 
  "asset": "string", 
  "borrowed": "string", 
  "free": "string", 
  "interest": "string", 
  "locked": "string", 
  "netAsset": "string" 
} 
 
MarginUserAssetVoSapiVersion
42.308. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
资产名称
borrowed
string
false
none
借款
free
string
false
none
可⽤余额
interest
string
false
none
利息
locked
string
false
none
锁定余额
netAsset
string
false
none
净资产


---

## Page 170

sapi-v7.4.md
2024-05-08
170 / 419
MarginUserMicroassets
{ 
  "operateTime": "2019-08-24T14:15:22Z", 
  "totalServiceChargeAmount": 0, 
  "totalTransferedAmount": 0, 
  "transId": 0, 
  "userAssetDribbletDetails": [ 
    { 
      "amount": 0, 
      "fromAsset": "string", 
      "operateTime": "2019-08-24T14:15:22Z", 
      "serviceChargeAmount": 0, 
      "transId": 0, 
      "transferedAmount": 0, 
      "uid": "string" 
    } 
  ] 
} 
 
MarginUserMicroassets
42.309. Properties
Name
Type
Required
Restrictions
Description
operateTime
string(date-time)
false
none
none
totalServiceChargeAmount
number
false
none
none
totalTransferedAmount
number
false
none
none
transId
integer(int64)
false
none
none
userAssetDribbletDetails
[MarginUserMicroassetsDetail]
false
none
none
MarginUserMicroassetsDetail
{ 
  "amount": 0, 
  "fromAsset": "string", 
  "operateTime": "2019-08-24T14:15:22Z", 
  "serviceChargeAmount": 0, 
  "transId": 0, 
  "transferedAmount": 0, 
  "uid": "string" 
} 
 
MarginUserMicroassetsDetail
42.310. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
fromAsset
string
false
none
none
operateTime
string(date-time)
false
none
none
serviceChargeAmount
number
false
none
none
transId
integer(int64)
false
none
none
transferedAmount
number
false
none
none
uid
string
false
none
none
MarkOrderAsPaidReq
{ 
  "orderNumber": "string", 
  "payId": 0 
} 
 


---

## Page 171

sapi-v7.4.md
2024-05-08
171 / 419
MarkOrderAsPaidReq
42.311. Properties
Name
Type
Required
Restrictions
Description
orderNumber
string
false
none
Order number
payId
integer(int64)
false
none
Payment method ID use for making payment
MarkOrderAsPaidResp
{ 
  "complainFreezeTime": "2019-08-24T14:15:22Z", 
  "confirmPayEndTime": "2019-08-24T14:15:22Z", 
  "notifyPayTime": "2019-08-24T14:15:22Z", 
  "orderNumber": "string", 
  "orderStatus": 0, 
  "selectedPayId": 0 
} 
 
MarkOrderAsPaidResp
42.312. Properties
Name
Type
Required
Restrictions
Description
complainFreezeTime
string(date-
time)
false
none
Complaint freeze time
confirmPayEndTime
string(date-
time)
false
none
Deadline for confirming receipt of payment
notifyPayTime
string(date-
time)
false
none
Time to send notification for payment
orderNumber
string
false
none
Order number
orderStatus
integer(int32)
false
none
Order status (1: Wait for payment, 2: Wait for release, 3: Appealing, 4: Completed, 6:
Cancelled, 7: Cancelled by system
selectedPayId
integer(int64)
false
none
Selected user payment ID
MarkOrderMessageAsReadReq
{ 
  "orderNo": "string", 
  "userId": 0 
} 
 
MarkOrderMessageAsReadReq
42.313. Properties
Name
Type
Required
Restrictions
Description
orderNo
string
false
none
Order number
userId
integer(int64)
false
none
User ID
MarketMakersResponse
{ 
  "cmMmLevel": "string", 
  "cmRebates": 0, 
  "curCmTaker": 0, 
  "curMmStatus": "string", 
  "curSpotTaker": 0, 
  "curUmTaker": 0, 
  "curVipLevel": 0, 
  "futuresVol30d": 0, 


---

## Page 172

sapi-v7.4.md
2024-05-08
172 / 419
  "ifCmMm": true, 
  "ifSpotMm": true, 
  "ifUmMm": true, 
  "spotMmLevel": "string", 
  "spotRebates": 0, 
  "spotVol30d": 0, 
  "umMmLevel": "string", 
  "umRebates": 0, 
  "userId": 0 
} 
 
MarketMakersResponse
42.314. Properties
Name
Type
Required
Restrictions
Description
cmMmLevel
string
false
none
none
cmRebates
number
false
none
none
curCmTaker
number
false
none
none
curMmStatus
string
false
none
none
curSpotTaker
number
false
none
none
curUmTaker
number
false
none
none
curVipLevel
integer(int32)
false
none
none
futuresVol30d
number
false
none
none
ifCmMm
boolean
false
none
none
ifSpotMm
boolean
false
none
none
ifUmMm
boolean
false
none
none
spotMmLevel
string
false
none
none
spotRebates
number
false
none
none
spotVol30d
number
false
none
none
umMmLevel
string
false
none
none
umRebates
number
false
none
none
userId
integer(int64)
false
none
none
MatchedDeposit
{ 
  "amount": "string", 
  "coin": "string", 
  "id": "string", 
  "network": "string", 
  "targetAddress": "string", 
  "txId": "string" 
} 
 
MatchedDeposit
42.315. Properties
Name
Type
Required
Restrictions
Description
amount
string
false
none
none
coin
string
false
none
none
id
string
false
none
none
network
string
false
none
none
targetAddress
string
false
none
none
txId
string
false
none
none


---

## Page 173

sapi-v7.4.md
2024-05-08
173 / 419
MerchantAdsDetailResp
{ 
  "buyList": [ 
    { 
      "adVisibleRet": { 
        "freeAmountVisible": 0, 
        "orderFlowVisible": 0, 
        "surplusAmountVisible": 0, 
        "userSetVisible": 0 
      }, 
      "advNo": "string", 
      "asset": "string", 
      "assetScale": 0, 
      "assetTicketSize": "string", 
      "autoReply": "string", 
      "buyerBtcAmount": 0, 
      "buyerRegisterLimit": 0, 
      "currencyTicketSize": "string", 
      "dynamicMaxOrderAmount": 0, 
      "dynamicMaxOrderPrice": 0, 
      "fiatScale": 0, 
      "fiatSymbol": "string", 
      "fiatUnit": "string", 
      "isConformed": true, 
      "kycLimit": 0, 
      "logo": "string", 
      "mainUserId": 0, 
      "maxOrderAmount": 0, 
      "maxOrderPrice": 0, 
      "minOrderAmount": 0, 
      "minOrderPrice": 0, 
      "offlineReason": "string", 
      "payMethodDtos": [ 
        { 
          "iconUrlColor": "string", 
          "id": 0, 
          "identifier": "string", 
          "payAccount": "string", 
          "payBank": "string", 
          "payMethodId": "string", 
          "paySubBank": "string", 
          "payType": "string", 
          "tradeMethodBgColor": "string", 
          "tradeMethodName": "string", 
          "tradeMethodShortName": "string" 
        } 
      ], 
      "payTimeLimit": 0, 
      "payTypeList": [ 
        "string" 
      ], 
      "price": 0, 
      "priceScale": 0, 
      "priceTicketSize": "string", 
      "remark": "string", 
      "surplusAmount": 0, 
      "takerAdditionalKycRequired": 0, 
      "tradeType": "BUY", 
      "userId": 0 
    } 
  ], 
  "merchant": { 
    "advConfirmTime": 0, 
    "assetTicketSize": "string", 
    "authentication": true, 
    "bindMobile": true, 
    "chanelInvolved": "string", 
    "emailVerified": true, 
    "firstOrderDays": 0, 
    "idVerified": true, 
    "margin": 0, 
    "marginUnit": "string", 
    "merchantNo": "string", 
    "monthFinishRate": 0, 
    "monthOrderCount": 0, 
    "nickColor": "string", 
    "nickName": "string", 
    "onlineStatus": "string", 


---

## Page 174

sapi-v7.4.md
2024-05-08
174 / 419
    "orderCount": 0, 
    "registerDays": 0, 
    "userGradeInstanceResp": { 
      "agreementSigned": 0, 
      "emailStatus": 0, 
      "kycStatus": 0, 
      "marginStatus": 0, 
      "mobileStatus": 0, 
      "nickNameStatus": 0, 
      "userGrade": 0 
    }, 
    "userKycResp": { 
      "addressStatus": "string", 
      "kycType": "string" 
    }, 
    "userNo": "string", 
    "userStatsResp": { 
      "avgPayTimeOfLatest30day": 0, 
      "avgReleaseTimeOfLatest30day": 0, 
      "completedBuyOrderNum": 0, 
      "completedBuyOrderNumOfLatest30day": 0, 
      "completedBuyOrderTotalBtcAmount": 0, 
      "completedOrderNum": 0, 
      "completedOrderNumOfLatest30day": 0, 
      "completedOrderTotalBtcAmount": 0, 
      "completedOrderTotalBtcAmountOfLatest30day": 0, 
      "completedSellOrderNum": 0, 
      "completedSellOrderNumOfLatest30day": 0, 
      "completedSellOrderTotalBtcAmount": 0, 
      "finishRateLatest30day": 0, 
      "firstOrderDays": 0, 
      "payMethodCount": 0, 
      "registerDays": 0 
    }, 
    "userType": "string" 
  }, 
  "sellList": [ 
    { 
      "adVisibleRet": { 
        "freeAmountVisible": 0, 
        "orderFlowVisible": 0, 
        "surplusAmountVisible": 0, 
        "userSetVisible": 0 
      }, 
      "advNo": "string", 
      "asset": "string", 
      "assetScale": 0, 
      "assetTicketSize": "string", 
      "autoReply": "string", 
      "buyerBtcAmount": 0, 
      "buyerRegisterLimit": 0, 
      "currencyTicketSize": "string", 
      "dynamicMaxOrderAmount": 0, 
      "dynamicMaxOrderPrice": 0, 
      "fiatScale": 0, 
      "fiatSymbol": "string", 
      "fiatUnit": "string", 
      "isConformed": true, 
      "kycLimit": 0, 
      "logo": "string", 
      "mainUserId": 0, 
      "maxOrderAmount": 0, 
      "maxOrderPrice": 0, 
      "minOrderAmount": 0, 
      "minOrderPrice": 0, 
      "offlineReason": "string", 
      "payMethodDtos": [ 
        { 
          "iconUrlColor": "string", 
          "id": 0, 
          "identifier": "string", 
          "payAccount": "string", 
          "payBank": "string", 
          "payMethodId": "string", 
          "paySubBank": "string", 
          "payType": "string", 
          "tradeMethodBgColor": "string", 
          "tradeMethodName": "string", 
          "tradeMethodShortName": "string" 
        } 
      ], 


---

## Page 175

sapi-v7.4.md
2024-05-08
175 / 419
      "payTimeLimit": 0, 
      "payTypeList": [ 
        "string" 
      ], 
      "price": 0, 
      "priceScale": 0, 
      "priceTicketSize": "string", 
      "remark": "string", 
      "surplusAmount": 0, 
      "takerAdditionalKycRequired": 0, 
      "tradeType": "BUY", 
      "userId": 0 
    } 
  ] 
} 
 
MerchantAdsDetailResp
42.316. Properties
Name
Type
Required
Restrictions
Description
buyList
[AdDetailVo]
false
none
List of buy adv
merchant
_MerchantDetailVo
false
none
Merchant detail
sellList
[AdDetailVo]
false
none
List of sell adv
MgsBorrowHistoryDtoV2
{ 
  "asset": "string", 
  "clientTag": "string", 
  "isolatedSymbol": "string", 
  "principal": 0, 
  "status": "CONFIRMED", 
  "timestamp": 0, 
  "txId": 0 
} 
 
MgsBorrowHistoryDtoV2
42.317. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
资⾦名称
clientTag
string
false
none
客户标记
isolatedSymbol
string
false
none
逐仓symbol
principal
number
false
none
借款⾦额
status
string
false
none
状态
timestamp
integer(int64)
false
none
借款时间
txId
integer(int64)
false
none
交易流⽔号
42.317.1. Enumerated Values
Property
Value
status
CONFIRMED
status
FAILED
status
PENDING
MgsRepayHistoryDtoV2
{ 
  "amount": 0, 
  "asset": "string", 


---

## Page 176

sapi-v7.4.md
2024-05-08
176 / 419
  "clientTag": "string", 
  "interest": 0, 
  "isolatedSymbol": "string", 
  "principal": 0, 
  "status": "CONFIRMED", 
  "timestamp": 0, 
  "txId": 0 
} 
 
MgsRepayHistoryDtoV2
42.318. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
还款⾦额
asset
string
false
none
资⾦名称
clientTag
string
false
none
客户标记
interest
number
false
none
偿还利息
isolatedSymbol
string
false
none
逐仓symbol
principal
number
false
none
偿还本⾦
status
string
false
none
状态
timestamp
integer(int64)
false
none
还款时间
txId
integer(int64)
false
none
交易流⽔号
42.318.1. Enumerated Values
Property
Value
status
CONFIRMED
status
FAILED
status
PENDING
MigrateLog
{ 
  "assetDetails": [ 
    { 
      "amount": 0, 
      "asset": "string" 
    } 
  ], 
  "migrateTime": 0, 
  "tranId": 0 
} 
 
MigrateLog
42.319. Properties
Name
Type
Required
Restrictions
Description
assetDetails
[NLAssetDetail]
false
none
asset details
migrateTime
integer(int64)
false
none
migrate time
tranId
integer(int64)
false
none
migrate tran id
MiningPoolCommonResp
{ 
  "code": 0, 
  "data": {}, 
  "msg": "string" 
} 
 


---

## Page 177

sapi-v7.4.md
2024-05-08
177 / 419
MiningPoolCommonResp
42.320. Properties
Name
Type
Required
Restrictions
Description
code
integer(int32)
false
none
none
data
object
false
none
none
msg
string
false
none
none
MinterInfo
{ 
  "country": "string", 
  "dob": "string", 
  "fullName": "string", 
  "state": "string" 
} 
 
MinterInfo
42.321. Properties
Name
Type
Required
Restrictions
Description
country
string
false
none
none
dob
string
false
none
none
fullName
string
false
none
none
state
string
false
none
none
MirrorWalletBalanceResp
{ 
  "totalBtc": 0 
} 
 
MirrorWalletBalanceResp
42.322. Properties
Name
Type
Required
Restrictions
Description
totalBtc
number
false
none
total btc
ModifyFundAutoIpRestrictResp
{ 
  "apiKey": "string", 
  "tradeIp": "string", 
  "withdrawIp": "string" 
} 
 
ModifyFundAutoIpRestrictResp
42.323. Properties
Name
Type
Required
Restrictions
Description
apiKey
string
false
none
none
tradeIp
string
false
none
none
withdrawIp
string
false
none
none


---

## Page 178

sapi-v7.4.md
2024-05-08
178 / 419
ModifySubFundAutoIpRestrictResp
{ 
  "apiKey": "string", 
  "tradeIp": "string", 
  "withdrawIp": "string" 
} 
 
ModifySubFundAutoIpRestrictResp
42.324. Properties
Name
Type
Required
Restrictions
Description
apiKey
string
false
none
none
tradeIp
string
false
none
none
withdrawIp
string
false
none
none
NLAssetDetail
{ 
  "amount": 0, 
  "asset": "string" 
} 
 
NLAssetDetail
42.325. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
asset amount like BTC
asset
string
false
none
asset code like BTC
NetworkCoinMappingResp
{ 
  "addressRegex": "string", 
  "addressRule": "string", 
  "busy": true, 
  "coin": "string", 
  "contractAddress": "string", 
  "contractAddressUrl": "string", 
  "country": "string", 
  "depositDesc": "string", 
  "depositDust": 0, 
  "depositEnable": true, 
  "entityTag": "string", 
  "estimatedArrivalTime": 0, 
  "isDefault": true, 
  "memoRegex": "string", 
  "minConfirm": 0, 
  "name": "string", 
  "network": "string", 
  "resetAddressStatus": true, 
  "sameAddress": true, 
  "specialTips": "string", 
  "specialWithdrawTips": "string", 
  "unLockConfirm": 0, 
  "withdrawDesc": "string", 
  "withdrawEnable": true, 
  "withdrawFee": 0, 
  "withdrawIntegerMultiple": 0, 
  "withdrawMax": 0, 
  "withdrawMin": 0 
} 
 
NetworkCoinMappingResp


---

## Page 179

sapi-v7.4.md
2024-05-08
179 / 419
42.326. Properties
Name
Type
Required
Restrictions
Description
addressRegex
string
false
none
none
addressRule
string
false
none
none
busy
boolean
false
none
none
coin
string
false
none
none
contractAddress
string
false
none
none
contractAddressUrl
string
false
none
none
country
string
false
none
none
depositDesc
string
false
none
none
depositDust
number
false
none
none
depositEnable
boolean
false
none
none
entityTag
string
false
none
none
estimatedArrivalTime
integer(int64)
false
none
none
isDefault
boolean
false
none
none
memoRegex
string
false
none
none
minConfirm
integer(int64)
false
none
none
name
string
false
none
none
network
string
false
none
none
resetAddressStatus
boolean
false
none
none
sameAddress
boolean
false
none
none
specialTips
string
false
none
none
specialWithdrawTips
string
false
none
none
unLockConfirm
integer(int64)
false
none
none
withdrawDesc
string
false
none
none
withdrawEnable
boolean
false
none
none
withdrawFee
number
false
none
none
withdrawIntegerMultiple
number
false
none
none
withdrawMax
number
false
none
none
withdrawMin
number
false
none
none
NewOrderResponse
{ 
  "clientAlgoId": "string", 
  "code": 0, 
  "msg": "string", 
  "success": true 
} 
 
NewOrderResponse
42.327. Properties
Name
Type
Required
Restrictions
Description
clientAlgoId
string
false
none
none
code
integer(int32)
false
none
none
msg
string
false
none
none
success
boolean
false
none
none
NextHourlyInterestRateResp


---

## Page 180

sapi-v7.4.md
2024-05-08
180 / 419
{ 
  "asset": "string", 
  "nextHourlyInterestRate": 0 
} 
 
NextHourlyInterestRateResp
42.328. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
nextHourlyInterestRate
number
false
none
none
OcbsRet
{ 
  "amount": 0, 
  "externalId": "string", 
  "msg": "string", 
  "objs": [ 
    {} 
  ], 
  "rows": {} 
} 
 
OcbsRet
42.329. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
externalId
string
false
none
第三⽅transaction Id
msg
string
false
none
none
objs
[object]
false
none
none
rows
object
false
none
none
OpenOrderResultResp
{ 
  "clientOrderId": "string", 
  "createDate": 0, 
  "executedQty": 0, 
  "orderId": 0, 
  "price": 0, 
  "quantity": 0, 
  "side": "BUY", 
  "status": "ACCEPTED", 
  "symbol": "string", 
  "timeInForce": "string", 
  "type": "CALL" 
} 
 
OpenOrderResultResp
42.330. Properties
Name
Type
Required
Restrictions
Description
clientOrderId
string
false
none
none
createDate
integer(int64)
false
none
none
executedQty
number
false
none
none
orderId
integer(int64)
false
none
none


---

## Page 181

sapi-v7.4.md
2024-05-08
181 / 419
Name
Type
Required
Restrictions
Description
price
number
false
none
none
quantity
number
false
none
none
side
string
false
none
none
status
string
false
none
none
symbol
string
false
none
none
timeInForce
string
false
none
none
type
string
false
none
none
42.330.1. Enumerated Values
Property
Value
side
BUY
side
SELL
status
ACCEPTED
status
CANCELLED
status
CANCELLING
status
CLOSING
status
DUPLICATE_CANCEL
status
ENDED
status
FILLED
status
NO_ORDER
status
OPEN
status
REJECTED
status
UNKNOWN
type
CALL
type
PUT
Order
{ 
  "orderId": 0 
} 
 
Order
42.331. Properties
Name
Type
Required
Restrictions
Description
orderId
integer(int64)
false
none
none
Order0
{ 
  "clientOrderId": "string", 
  "code": 0, 
  "confirmedTime": 0, 
  "createTime": 0, 
  "expiryTime": 0, 
  "msg": "string", 
  "orderId": 0, 
  "orderStatus": "string", 
  "price": 0, 
  "quantity": 0, 
  "quoteAsset": "string", 
  "settleTime": 0, 
  "strikePrice": 0, 


---

## Page 182

sapi-v7.4.md
2024-05-08
182 / 419
  "timeInForce": "string", 
  "type": "string", 
  "underlying": "string" 
} 
 
Order0
42.332. Properties
Name
Type
Required
Restrictions
Description
clientOrderId
string
false
none
none
code
integer(int32)
false
none
none
confirmedTime
integer(int64)
false
none
none
createTime
integer(int64)
false
none
none
expiryTime
integer(int64)
false
none
none
msg
string
false
none
none
orderId
integer(int64)
false
none
none
orderStatus
string
false
none
none
price
number
false
none
none
quantity
number
false
none
none
quoteAsset
string
false
none
none
settleTime
integer(int64)
false
none
none
strikePrice
number
false
none
none
timeInForce
string
false
none
none
type
string
false
none
none
underlying
string
false
none
none
OrderAdditionalKycVerifyResp
{ 
  "kycVerified": true, 
  "orderNumber": "string" 
} 
 
OrderAdditionalKycVerifyResp
42.333. Properties
Name
Type
Required
Restrictions
Description
kycVerified
boolean
false
none
order additional kyc verified: true false
orderNumber
string
false
none
order number
OrderFill
{ 
  "commission": 0, 
  "commissionAsset": "string", 
  "price": 0, 
  "qty": 0, 
  "tradeId": 0 
} 
 
OrderFill
42.334. Properties
Name
Type
Required
Restrictions
Description


---

## Page 183

sapi-v7.4.md
2024-05-08
183 / 419
Name
Type
Required
Restrictions
Description
commission
number
false
none
none
commissionAsset
string
false
none
none
price
number
false
none
none
qty
number
false
none
none
tradeId
integer(int64)
false
none
none
OrderItem
{ 
  "asc": true, 
  "column": "string" 
} 
 
OrderItem
42.335. Properties
Name
Type
Required
Restrictions
Description
asc
boolean
false
none
none
column
string
false
none
none
OrderMatchListResp
{ 
  "additionalKycVerify": 0, 
  "advNo": "string", 
  "amount": "string", 
  "asset": "string", 
  "assetTicketSize": "string", 
  "buyerNickname": "string", 
  "chatUnreadCount": 0, 
  "commission": 0, 
  "commissionRate": 0, 
  "confirmPayEndTime": "2019-08-24T14:15:22Z", 
  "createTime": "2019-08-24T14:15:22Z", 
  "currencyTicketSize": "string", 
  "fiat": "string", 
  "fiatSymbol": "string", 
  "notifyPayEndTime": "2019-08-24T14:15:22Z", 
  "orderNumber": "string", 
  "orderStatus": 0, 
  "priceTicketSize": "string", 
  "sellerNickname": "string", 
  "takerAmount": 0, 
  "takerCommission": 0, 
  "takerCommissionRate": 0, 
  "totalPrice": "string", 
  "tradeMethodCommissionRateVoList": [ 
    { 
      "commissionRate": 0, 
      "tradeMethodIdentifier": "string", 
      "tradeMethodName": "string" 
    } 
  ], 
  "tradeType": "string" 
} 
 
OrderMatchListResp
42.336. Properties
Name
Type
Required
Restrictions
Description
additionalKycVerify
integer(int32)
false
none
additional kyc verify: 0 not required 1 not verified 2
verified


---

## Page 184

sapi-v7.4.md
2024-05-08
184 / 419
Name
Type
Required
Restrictions
Description
advNo
string
false
none
Adv number
amount
string
false
none
seller/buyer trade amount = (seller deducted amount -
seller fee amount) = (buyer received amount + buyer
fee amount)
asset
string
false
none
Crypto asset: BTC
assetTicketSize
string
false
none
Asset currency decimal precision
buyerNickname
string
false
none
Buyer nickname
chatUnreadCount
integer(int32)
false
none
Number of unread chat messages
commission
number
false
none
Actual commission fee of order
commissionRate
number
false
none
Order commission rate
confirmPayEndTime
string(date-time)
false
none
Deadline for confirming receipt of payment
createTime
string(date-time)
false
none
Order create time
currencyTicketSize
string
false
none
Fiat currency decimal precision
fiat
string
false
none
Fiat currency: CNY
fiatSymbol
string
false
none
Fiat currency symbol
notifyPayEndTime
string(date-time)
false
none
Deadline for confirming payment
orderNumber
string
false
none
Order number
orderStatus
integer(int32)
false
none
Order status (1: Wait for payment, 2: Wait for release, 3:
Appealing, 4: Completed, 6: Cancelled, 7: Cancelled by
system)
priceTicketSize
string
false
none
Price decimal precision
sellerNickname
string
false
none
Seller nickname
takerAmount
number
false
none
taker actual deducted/received amount if taker sell:
taker amount = seller deducted amount = (amount +
taker_commission), if taker buy: taker amount = buyer
received amount = (amount - taker_commission)
takerCommission
number
false
none
taker actual commission
takerCommissionRate
number
false
none
taker actual commission rate
totalPrice
string
false
none
Order total price
tradeMethodCommissionRateVoList
[TradeMethodCommissionRateVo]
false
none
Commission rate for each payment method
tradeType
string
false
none
Order trade type. 0: BUY, 1: SELL
OrderMatchResp
{ 
  "additionalKycVerify": 0, 
  "address": "string", 
  "advMainUserId": 0, 
  "advMakerRoles": "string", 
  "advOrderId": 0, 
  "advOrderNumber": "string", 
  "advUserId": 0, 
  "allowComplainTime": "2019-08-24T14:15:22Z", 
  "amount": 0, 
  "asset": "string", 
  "assetTicketSize": "string", 
  "buyerCompanyAccountName": "string", 
  "buyerCreditScore": 0, 
  "buyerMobilePhone": "string", 
  "buyerName": "string", 
  "buyerNickname": "string", 
  "canCancelComplaintOrder": true, 
  "cancelComplaintTime": "2019-08-24T14:15:22Z", 
  "cancelReasonAdditional": "string", 
  "cancelReasonDesc": "string", 
  "cancelTime": "2019-08-24T14:15:22Z", 
  "chatUnreadCount": 0, 
  "classify": "string", 
  "clientType": "string", 


---

## Page 185

sapi-v7.4.md
2024-05-08
185 / 419
  "commission": 0, 
  "commissionRate": 0, 
  "complainFreezeTime": "2019-08-24T14:15:22Z", 
  "complaintDeadline": "2019-08-24T14:15:22Z", 
  "complaintReason": "string", 
  "complaintStatus": 0, 
  "confirmPaidType": "string", 
  "confirmPayEndTime": "2019-08-24T14:15:22Z", 
  "confirmPayTime": "2019-08-24T14:15:22Z", 
  "confirmPayTimeout": 0, 
  "confirmPayedExpireMinute": 0, 
  "createTime": "2019-08-24T14:15:22Z", 
  "currencyRate": 0, 
  "currencyTicketSize": "string", 
  "fiatSymbol": "string", 
  "fiatUnit": "string", 
  "idNumber": "string", 
  "isBuyerCompanyAccount": true, 
  "isChatEnabled": true, 
  "isComplaintAllowed": true, 
  "isRiskCount": 0, 
  "isSellerCompanyAccount": true, 
  "isSupportVirtualNum": true, 
  "lengthOfConfirmTime": 0, 
  "lengthOfPayTime": 0, 
  "mainUserId": 0, 
  "maker": { 
    "advConfirmTime": 0, 
    "badges": [ 
      "string" 
    ], 
    "businessMobile": "string", 
    "businessStatus": 0, 
    "complaintCount": 0, 
    "countyCode": "string", 
    "createTime": "2019-08-24T14:15:22Z", 
    "email": "string", 
    "eqMargin": 0, 
    "eqMarginUnit": "string", 
    "fiatTradingAccount": 0, 
    "firstOrderDays": 0, 
    "fundpwdStatus": 0, 
    "id": 0, 
    "informMethods": "string", 
    "maliceInitiatorCount": 0, 
    "margin": 0, 
    "marginAsset": { 
      "asset": "string", 
      "createTime": "2019-08-24T14:15:22Z", 
      "decimalScale": 0, 
      "iconUrl": "string", 
      "isEnable": 0, 
      "isTransVisible": 0, 
      "name": "string", 
      "ranking": 0, 
      "updateTime": "2019-08-24T14:15:22Z" 
    }, 
    "marginFreeze": 0, 
    "marginStatsItems": [ 
      { 
        "margin": 0, 
        "marginUnit": "string" 
      } 
    ], 
    "marginUnit": "string", 
    "maskedBusinessMobile": "string", 
    "maskedEmail": "string", 
    "merchantType": "string", 
    "mobile": "string", 
    "mobileDisplayStatus": 0, 
    "monthFinishRate": 0, 
    "monthOrderCount": 0, 
    "nickColor": "string", 
    "nickName": "string", 
    "onlineStatus": 0, 
    "orderCount": 0, 
    "overComplained": 0, 
    "parentId": 0, 
    "payMethodCount": 0, 
    "proMerchantVo": { 
      "merchantDescription": "string", 


---

## Page 186

sapi-v7.4.md
2024-05-08
186 / 419
      "merchantLogo": "string" 
    }, 
    "realName": "string", 
    "registerDays": 0, 
    "registrationTime": "2019-08-24T14:15:22Z", 
    "tradingAccount": 0, 
    "updateTime": "2019-08-24T14:15:22Z", 
    "userGradeInstanceVo": { 
      "agreementSigned": 0, 
      "authorityId": 0, 
      "createTime": "2019-08-24T14:15:22Z", 
      "emailStatus": 0, 
      "id": 0, 
      "kycStatus": 0, 
      "marginStatus": 0, 
      "mobileStatus": 0, 
      "nickNameStatus": 0, 
      "parentId": 0, 
      "qualificationId": 0, 
      "updateTime": "2019-08-24T14:15:22Z", 
      "userGradeQualificationVo": { 
        "accountGrade": 0, 
        "accountType": 0, 
        "agreement": 0, 
        "countryCode": "string", 
        "createTime": "2019-08-24T14:15:22Z", 
        "defaultAuthority": 0, 
        "email": 0, 
        "gradeName": "string", 
        "id": 0, 
        "kycVerify": 0, 
        "margin": 0, 
        "mobile": 0, 
        "nickName": 0, 
        "typeName": "string", 
        "updateTime": "2019-08-24T14:15:22Z" 
      }, 
      "userId": 0 
    }, 
    "userId": 0, 
    "userKycVo": { 
      "address": "string", 
      "addressStatus": "string", 
      "basicStatus": "string", 
      "certificateStatus": 0, 
      "companyName": "string", 
      "countyCode": "string", 
      "createTime": "2019-08-24T14:15:22Z", 
      "faceStatus": "string", 
      "firstName": "string", 
      "idNo": "string", 
      "identityStatus": "string", 
      "kycLevel": 0, 
      "kycStatus": "string", 
      "kycType": "string", 
      "lastName": "string", 
      "middleName": "string", 
      "updateTime": "2019-08-24T14:15:22Z", 
      "userId": 0 
    }, 
    "userNo": "string", 
    "userOrderHistoryStatsVo": { 
      "accountAge": 0, 
      "appealedOrderCountHistorical": 0, 
      "appealedOrderCountLast30Days": 0, 
      "appealedRateHistorical": 0, 
      "appealedRateLast30Days": 0, 
      "avgPayTime": 0, 
      "avgPayTimeOfLatest30day": 0, 
      "avgReleaseTime": 0, 
      "avgReleaseTimeOfLatest30day": 0, 
      "buyOrderNum": 0, 
      "buyOrderNumOfLatest30day": 0, 
      "canceledBuyOrderNum": 0, 
      "canceledBuyOrderNumOfLatest30day": 0, 
      "completedBuyOrderNum": 0, 
      "completedBuyOrderNumOfLatest30day": 0, 
      "completedBuyOrderTotalBtcAmount": 0, 
      "completedBuyOrderTotalBtcAmountOfLatest30day": 0, 
      "completedOrderNum": 0, 
      "completedOrderNumOfLatest30day": 0, 


---

## Page 187

sapi-v7.4.md
2024-05-08
187 / 419
      "completedOrderTotalBtcAmount": 0, 
      "completedOrderTotalBtcAmountOfLatest30day": 0, 
      "completedSellOrderNum": 0, 
      "completedSellOrderNumOfLatest30day": 0, 
      "completedSellOrderTotalBtcAmount": 0, 
      "completedSellOrderTotalBtcAmountOfLatest30day": 0, 
      "counterpartyNum": 0, 
      "creditScore": 0, 
      "finishRate": 0, 
      "finishRateLatest30Day": 0 
    }, 
    "userOrderInProgressStatsVo": { 
      "buyerPayedCount": 0, 
      "inAppealCount": 0, 
      "inAppealCountAfterBuyerPaid": 0, 
      "inAppealCountAfterCancelled": 0, 
      "inAppealCountAfterCancelledBySystem": 0, 
      "inAppealCountAfterCompleted": 0, 
      "inProcessCount": 0, 
      "tradingCount": 0, 
      "userId": 0 
    }, 
    "userType": "string" 
  }, 
  "merchantNo": "string", 
  "nickColor": "string", 
  "notifyPayEndTime": "2019-08-24T14:15:22Z", 
  "notifyPayTime": "2019-08-24T14:15:22Z", 
  "notifyPayedExpireMinute": 0, 
  "onlineStatus": "string", 
  "orderComplaintAmount": { 
    "complaintAmount": 0, 
    "completedComplaintAmount": 0, 
    "processingComplaintAmount": 0 
  }, 
  "orderNumber": "string", 
  "orderStatus": 0, 
  "orderTakerRoles": "string", 
  "origin": "string", 
  "payAccount": "string", 
  "payBank": "string", 
  "payMethods": [ 
    { 
      "advCount": 0, 
      "createTime": "2019-08-24T14:15:22Z", 
      "currentPayAmount": 0, 
      "fieldList": [ 
        { 
          "createTime": "2019-08-24T14:15:22Z", 
          "errorKey": "string", 
          "errorWord": "string", 
          "fieldContentType": "string", 
          "fieldId": "string", 
          "fieldName": "string", 
          "fieldTitle": "string", 
          "fieldTitleKey": "string", 
          "fieldValue": "string", 
          "hintKey": "string", 
          "hintWord": "string", 
          "id": 0, 
          "isCopyable": 0, 
          "isDisplay": 0, 
          "isEncrypt": 0, 
          "isRequired": 0, 
          "lengthLimit": 0, 
          "restrictionType": 0, 
          "sequence": 0, 
          "status": 0, 
          "updateTime": "2019-08-24T14:15:22Z" 
        } 
      ], 
      "iconUrlColor": "string", 
      "id": 0, 
      "isRemoved": 0, 
      "mainUserId": 0, 
      "online": true, 
      "payLimit": 0, 
      "payLimitUnit": "string", 
      "payStatus": "ACTIVE", 
      "tradeMethodBgColor": "string", 
      "tradeMethodIdentifier": "string", 


---

## Page 188

sapi-v7.4.md
2024-05-08
188 / 419
      "tradeMethodName": "string", 
      "tradeMethodRisk": "string", 
      "tradeMethodShortName": "string", 
      "updateTime": "2019-08-24T14:15:22Z", 
      "userId": 0 
    } 
  ], 
  "paySubBank": "string", 
  "payTimeLimit": 0, 
  "payType": "string", 
  "payTypeDesc": "string", 
  "payee": "string", 
  "price": 0, 
  "priceTicketSize": "string", 
  "publisherType": "string", 
  "qrCodePath": "string", 
  "quickConfirmAmountUpLimit": 0, 
  "remark": "string", 
  "selectedPayId": 0, 
  "sellerCompanyAccountName": "string", 
  "sellerCreditScore": 0, 
  "sellerMobilePhone": "string", 
  "sellerName": "string", 
  "sellerNickname": "string", 
  "statFlag": 0, 
  "store": { 
    "applyStatus": 0, 
    "availableMargin": 0, 
    "countryCode": "string", 
    "distance": 0, 
    "enable": "string", 
    "fineAmount": 0, 
    "friOpenTime": "string", 
    "friOpenTimeLocal": "string", 
    "fullAddress": "string", 
    "geoCode": "string", 
    "latitude": 0, 
    "longitude": 0, 
    "margin": 0, 
    "marginFreeze": 0, 
    "marginUnit": "string", 
    "monOpenTime": "string", 
    "monOpenTimeLocal": "string", 
    "processingAmount": 0, 
    "refundProcessingAmount": 0, 
    "refundableFineAmount": 0, 
    "remark": "string", 
    "satOpenTime": "string", 
    "satOpenTimeLocal": "string", 
    "status": 0, 
    "storeAddressVo": { 
      "building": "string", 
      "city": "string", 
      "country": "string", 
      "flat": "string", 
      "floor": "string", 
      "province": "string", 
      "remark": "string", 
      "street": "string", 
      "zipCode": "string" 
    }, 
    "storeId": 0, 
    "storeMaterialItemVoList": [ 
      { 
        "dataFrom": "string", 
        "dataType": "string", 
        "fileType": "string", 
        "id": 0, 
        "itemData": "string", 
        "itemIdentifier": "string", 
        "storeId": 0 
      } 
    ], 
    "storeName": "string", 
    "storeShortName": "string", 
    "submissionTime": "2019-08-24T14:15:22Z", 
    "sunOpenTime": "string", 
    "sunOpenTimeLocal": "string", 
    "thuOpenTime": "string", 
    "thuOpenTimeLocal": "string", 
    "timeZone": "string", 


---

## Page 189

sapi-v7.4.md
2024-05-08
189 / 419
    "tueOpenTime": "string", 
    "tueOpenTimeLocal": "string", 
    "updateTime": "2019-08-24T14:15:22Z", 
    "userId": 0, 
    "valid": true, 
    "wedOpenTime": "string", 
    "wedOpenTimeLocal": "string" 
  }, 
  "sysCancelTime": "2019-08-24T14:15:22Z", 
  "taker": { 
    "advConfirmTime": 0, 
    "badges": [ 
      "string" 
    ], 
    "businessMobile": "string", 
    "businessStatus": 0, 
    "complaintCount": 0, 
    "countyCode": "string", 
    "createTime": "2019-08-24T14:15:22Z", 
    "email": "string", 
    "eqMargin": 0, 
    "eqMarginUnit": "string", 
    "fiatTradingAccount": 0, 
    "firstOrderDays": 0, 
    "fundpwdStatus": 0, 
    "id": 0, 
    "informMethods": "string", 
    "maliceInitiatorCount": 0, 
    "margin": 0, 
    "marginAsset": { 
      "asset": "string", 
      "createTime": "2019-08-24T14:15:22Z", 
      "decimalScale": 0, 
      "iconUrl": "string", 
      "isEnable": 0, 
      "isTransVisible": 0, 
      "name": "string", 
      "ranking": 0, 
      "updateTime": "2019-08-24T14:15:22Z" 
    }, 
    "marginFreeze": 0, 
    "marginStatsItems": [ 
      { 
        "margin": 0, 
        "marginUnit": "string" 
      } 
    ], 
    "marginUnit": "string", 
    "maskedBusinessMobile": "string", 
    "maskedEmail": "string", 
    "merchantType": "string", 
    "mobile": "string", 
    "mobileDisplayStatus": 0, 
    "monthFinishRate": 0, 
    "monthOrderCount": 0, 
    "nickColor": "string", 
    "nickName": "string", 
    "onlineStatus": 0, 
    "orderCount": 0, 
    "overComplained": 0, 
    "parentId": 0, 
    "payMethodCount": 0, 
    "proMerchantVo": { 
      "merchantDescription": "string", 
      "merchantLogo": "string" 
    }, 
    "realName": "string", 
    "registerDays": 0, 
    "registrationTime": "2019-08-24T14:15:22Z", 
    "tradingAccount": 0, 
    "updateTime": "2019-08-24T14:15:22Z", 
    "userGradeInstanceVo": { 
      "agreementSigned": 0, 
      "authorityId": 0, 
      "createTime": "2019-08-24T14:15:22Z", 
      "emailStatus": 0, 
      "id": 0, 
      "kycStatus": 0, 
      "marginStatus": 0, 
      "mobileStatus": 0, 
      "nickNameStatus": 0, 


---

## Page 190

sapi-v7.4.md
2024-05-08
190 / 419
      "parentId": 0, 
      "qualificationId": 0, 
      "updateTime": "2019-08-24T14:15:22Z", 
      "userGradeQualificationVo": { 
        "accountGrade": 0, 
        "accountType": 0, 
        "agreement": 0, 
        "countryCode": "string", 
        "createTime": "2019-08-24T14:15:22Z", 
        "defaultAuthority": 0, 
        "email": 0, 
        "gradeName": "string", 
        "id": 0, 
        "kycVerify": 0, 
        "margin": 0, 
        "mobile": 0, 
        "nickName": 0, 
        "typeName": "string", 
        "updateTime": "2019-08-24T14:15:22Z" 
      }, 
      "userId": 0 
    }, 
    "userId": 0, 
    "userKycVo": { 
      "address": "string", 
      "addressStatus": "string", 
      "basicStatus": "string", 
      "certificateStatus": 0, 
      "companyName": "string", 
      "countyCode": "string", 
      "createTime": "2019-08-24T14:15:22Z", 
      "faceStatus": "string", 
      "firstName": "string", 
      "idNo": "string", 
      "identityStatus": "string", 
      "kycLevel": 0, 
      "kycStatus": "string", 
      "kycType": "string", 
      "lastName": "string", 
      "middleName": "string", 
      "updateTime": "2019-08-24T14:15:22Z", 
      "userId": 0 
    }, 
    "userNo": "string", 
    "userOrderHistoryStatsVo": { 
      "accountAge": 0, 
      "appealedOrderCountHistorical": 0, 
      "appealedOrderCountLast30Days": 0, 
      "appealedRateHistorical": 0, 
      "appealedRateLast30Days": 0, 
      "avgPayTime": 0, 
      "avgPayTimeOfLatest30day": 0, 
      "avgReleaseTime": 0, 
      "avgReleaseTimeOfLatest30day": 0, 
      "buyOrderNum": 0, 
      "buyOrderNumOfLatest30day": 0, 
      "canceledBuyOrderNum": 0, 
      "canceledBuyOrderNumOfLatest30day": 0, 
      "completedBuyOrderNum": 0, 
      "completedBuyOrderNumOfLatest30day": 0, 
      "completedBuyOrderTotalBtcAmount": 0, 
      "completedBuyOrderTotalBtcAmountOfLatest30day": 0, 
      "completedOrderNum": 0, 
      "completedOrderNumOfLatest30day": 0, 
      "completedOrderTotalBtcAmount": 0, 
      "completedOrderTotalBtcAmountOfLatest30day": 0, 
      "completedSellOrderNum": 0, 
      "completedSellOrderNumOfLatest30day": 0, 
      "completedSellOrderTotalBtcAmount": 0, 
      "completedSellOrderTotalBtcAmountOfLatest30day": 0, 
      "counterpartyNum": 0, 
      "creditScore": 0, 
      "finishRate": 0, 
      "finishRateLatest30Day": 0 
    }, 
    "userOrderInProgressStatsVo": { 
      "buyerPayedCount": 0, 
      "inAppealCount": 0, 
      "inAppealCountAfterBuyerPaid": 0, 
      "inAppealCountAfterCancelled": 0, 
      "inAppealCountAfterCancelledBySystem": 0, 


---

## Page 191

sapi-v7.4.md
2024-05-08
191 / 419
      "inAppealCountAfterCompleted": 0, 
      "inProcessCount": 0, 
      "tradingCount": 0, 
      "userId": 0 
    }, 
    "userType": "string" 
  }, 
  "takerAmount": 0, 
  "takerCommission": 0, 
  "takerCommissionRate": 0, 
  "totalPrice": 0, 
  "tradeMethodCommissionRateVoList": [ 
    { 
      "commissionRate": 0, 
      "tradeMethodIdentifier": "string", 
      "tradeMethodName": "string" 
    } 
  ], 
  "tradeType": "BUY", 
  "unreadCount": 0, 
  "updateTime": "2019-08-24T14:15:22Z", 
  "userId": 0 
} 
 
OrderMatchResp
42.337. Properties
Name
Type
Required
Restrictions
Description
additionalKycVerify
integer(int32)
false
none
additional kyc verify: 0 not required 1 not verified 2
verified
address
string
false
none
none
advMainUserId
integer(int64)
false
none
⼴告商id
advMakerRoles
string
false
none
⼴告⽅maker身份，⽤户user，商户merchant
advOrderId
integer(int64)
false
none
none
advOrderNumber
string
false
none
none
advUserId
integer(int64)
false
none
none
allowComplainTime
string(date-time)
false
none
none
amount
number
false
none
none
asset
string
false
none
none
assetTicketSize
string
false
none
none
buyerCompanyAccountName
string
false
none
none
buyerCreditScore
number(double)
false
none
buyer 信⽤分 快照
buyerMobilePhone
string
false
none
none
buyerName
string
false
none
none
buyerNickname
string
false
none
none
canCancelComplaintOrder
boolean
false
none
none
cancelComplaintTime
string(date-time)
false
none
none
cancelReasonAdditional
string
false
none
none
cancelReasonDesc
string
false
none
none
cancelTime
string(date-time)
false
none
none
chatUnreadCount
integer(int32)
false
none
chat未读信息数量
classify
string
false
none
⼤宗交易block，普通交易mass，专业交易profession
clientType
string
false
none
none
commission
number
false
none
当前⼿续费
commissionRate
number
false
none
当前费率
complainFreezeTime
string(date-time)
false
none
none


---

## Page 192

sapi-v7.4.md
2024-05-08
192 / 419
Name
Type
Required
Restrictions
Description
complaintDeadline
string(date-time)
false
none
none
complaintReason
string
false
none
none
complaintStatus
integer(int32)
false
none
none
confirmPaidType
string
false
none
none
confirmPayEndTime
string(date-time)
false
none
none
confirmPayTime
string(date-time)
false
none
none
confirmPayTimeout
integer(int32)
false
none
none
confirmPayedExpireMinute
integer(int32)
false
none
none
createTime
string(date-time)
false
none
none
currencyRate
number
false
none
none
currencyTicketSize
string
false
none
none
fiatSymbol
string
false
none
none
fiatUnit
string
false
none
none
idNumber
string
false
none
none
isBuyerCompanyAccount
boolean
false
none
none
isChatEnabled
boolean
false
none
none
isComplaintAllowed
boolean
false
none
none
isRiskCount
integer(int32)
false
none
0,不计⼊⻛控 1,计⼊⻛控
isSellerCompanyAccount
boolean
false
none
none
isSupportVirtualNum
boolean
false
none
none
lengthOfConfirmTime
integer(int64)
false
none
放⾏时⻓
lengthOfPayTime
integer(int64)
false
none
付款时⻓
mainUserId
integer(int64)
false
none
none
maker
UserVo
false
none
none
merchantNo
string
false
none
none
nickColor
string
false
none
none
notifyPayEndTime
string(date-time)
false
none
none
notifyPayTime
string(date-time)
false
none
none
notifyPayedExpireMinute
integer(int32)
false
none
none
onlineStatus
string
false
none
none
orderComplaintAmount
_7
false
none
订单申诉数量
orderNumber
string
false
none
none
orderStatus
integer(int32)
false
none
none
orderTakerRoles
string
false
none
接单⽅taker身份，⽤户user，商户merchant
origin
string
false
none
订单来源：
payAccount
string
false
none
none
payBank
string
false
none
none
payMethods
[PayMethodVO]
false
none
none
paySubBank
string
false
none
none
payTimeLimit
integer(int32)
false
none
none
payType
string
false
none
none
payTypeDesc
string
false
none
none
payee
string
false
none
none
price
number
false
none
none
priceTicketSize
string
false
none
none


---

## Page 193

sapi-v7.4.md
2024-05-08
193 / 419
Name
Type
Required
Restrictions
Description
publisherType
string
false
none
发⼴告者类型，⽤户user，商户merchant
qrCodePath
string
false
none
none
quickConfirmAmountUpLimit
number
false
none
订单允许快速放⾏订单⾦额上限, 单位法币
remark
string
false
none
none
selectedPayId
integer(int64)
false
none
none
sellerCompanyAccountName
string
false
none
none
sellerCreditScore
number(double)
false
none
seller 信⽤分 快照
sellerMobilePhone
string
false
none
none
sellerName
string
false
none
none
sellerNickname
string
false
none
none
statFlag
integer(int32)
false
none
0,不计⼊统计 1,计⼊统计
store
StoreVo
false
none
none
sysCancelTime
string(date-time)
false
none
none
taker
UserVo
false
none
none
takerAmount
number
false
none
taker actual amount， if taker sell: seller deducted
amount = amount + taker_commission, if taker buy:
buyer received amount = amount - taker_commission
takerCommission
number
false
none
taker actual commission
takerCommissionRate
number
false
none
taker actual commission rate
totalPrice
number
false
none
none
tradeMethodCommissionRateVoList
[TradeMethodCommissionRateVo]
false
none
⽀付⽅式费率
tradeType
string
false
none
none
unreadCount
integer(int32)
false
none
消息未读数量
updateTime
string(date-time)
false
none
none
userId
integer(int64)
false
none
none
42.337.1. Enumerated Values
Property
Value
tradeType
BUY
tradeType
SELL
OrderMatchResp0
{ 
  "additionalKycVerify": 0, 
  "address": "string", 
  "advOrderId": 0, 
  "advOrderNumber": "string", 
  "allowComplainTime": "2019-08-24T14:15:22Z", 
  "amount": 0, 
  "asset": "string", 
  "assetTicketSize": "string", 
  "authentication": true, 
  "avgPayPeriod": 0, 
  "avgReleasePeriod": 0, 
  "buyerMobilePhone": "string", 
  "buyerName": "string", 
  "buyerNickname": "string", 
  "canCancelComplaintOrder": true, 
  "cancelTime": "2019-08-24T14:15:22Z", 
  "clientType": "string", 
  "commission": 0, 
  "commissionRate": 0, 
  "complainFreezeTime": "2019-08-24T14:15:22Z", 
  "complaintDeadline": "2019-08-24T14:15:22Z", 
  "complaintReason": "string", 
  "complaintStatus": 0, 


---

## Page 194

sapi-v7.4.md
2024-05-08
194 / 419
  "confirmPayEndTime": "2019-08-24T14:15:22Z", 
  "confirmPayTime": "2019-08-24T14:15:22Z", 
  "confirmPayTimeout": 0, 
  "confirmPayedExpireMinute": 0, 
  "createTime": "2019-08-24T14:15:22Z", 
  "currencyRate": 0, 
  "currencyTicketSize": "string", 
  "expectedPayTime": "2019-08-24T14:15:22Z", 
  "expectedReleaseTime": "2019-08-24T14:15:22Z", 
  "fiatSymbol": "string", 
  "fiatUnit": "string", 
  "iconUrl": "string", 
  "idNumber": "string", 
  "isComplaintAllowed": true, 
  "merchantNo": "string", 
  "nickColor": "string", 
  "notifyPayEndTime": "2019-08-24T14:15:22Z", 
  "notifyPayTime": "2019-08-24T14:15:22Z", 
  "notifyPayedExpireMinute": 0, 
  "onlineStatus": "string", 
  "orderNumber": "string", 
  "orderStatus": 0, 
  "origin": "string", 
  "payAccount": "string", 
  "payBank": "string", 
  "payMethods": [ 
    { 
      "fields": [ 
        { 
          "fieldContentType": "string", 
          "fieldId": "string", 
          "fieldName": "string", 
          "fieldValue": "string", 
          "hintWord": "string", 
          "isCopyable": true, 
          "isRequired": true, 
          "lengthLimit": 0, 
          "restrictionType": 0, 
          "sequence": 0 
        } 
      ], 
      "iconUrlColor": "string", 
      "id": 0, 
      "identifier": "string", 
      "tradeMethodName": "string" 
    } 
  ], 
  "paySubBank": "string", 
  "payType": "string", 
  "payee": "string", 
  "price": 0, 
  "priceTicketSize": "string", 
  "qrCodePath": "string", 
  "remark": "string", 
  "selectedPayId": 0, 
  "sellerMobilePhone": "string", 
  "sellerName": "string", 
  "sellerNickname": "string", 
  "takerAmount": 0, 
  "takerCommission": 0, 
  "takerCommissionRate": 0, 
  "totalPrice": 0, 
  "tradeMethodCommissionRateVoList": [ 
    { 
      "commissionRate": 0, 
      "tradeMethodIdentifier": "string", 
      "tradeMethodName": "string" 
    } 
  ], 
  "tradeType": "BUY", 
  "unreadCount": 0, 
  "updateTime": "2019-08-24T14:15:22Z" 
} 
 
OrderMatchResp0
42.338. Properties


---

## Page 195

sapi-v7.4.md
2024-05-08
195 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
additionalKycVerify
integer(int32)
false
none
additional kyc verify: 0 not required 1 not verified 2
verified
address
string
false
none
Address provided by individual during identity
verification
advOrderId
integer(int64)
false
none
Adv id
advOrderNumber
string
false
none
Adv number
allowComplainTime
string(date-time)
false
none
Deadline for allowing complaint for this order
amount
number
false
none
seller/buyer trade amount = (seller deducted amount -
seller fee amount) = (buyer received amount + buyer
fee amount)
asset
string
false
none
Crypto asset: BTC
assetTicketSize
string
false
none
Asset currency decimal precision
authentication
boolean
false
none
If the user is an authenticated merchant
avgPayPeriod
integer(int32)
false
none
Average payment time
avgReleasePeriod
integer(int32)
false
none
Average release time
buyerMobilePhone
string
false
none
Buyer mobile number
buyerName
string
false
none
Buyer name
buyerNickname
string
false
none
Buyer nickname
canCancelComplaintOrder
boolean
false
none
If the current user can cancel the complaint order,
during order in appeal
cancelTime
string(date-time)
false
none
Cancellation time if order is cancelled
clientType
string
false
none
Client type (web, ios, android)
commission
number
false
none
Actual commission fee of order
commissionRate
number
false
none
Commission rate of order
complainFreezeTime
string(date-time)
false
none
Deadline for complaint freezing time
complaintDeadline
string(date-time)
false
none
Complaint deadline for both parties waiting for the
other party to handle
complaintReason
string
false
none
Complaint reason
complaintStatus
integer(int32)
false
none
Complaint status (0: Respondent In Progress, 1:
Compliant In Progress, 2: In process, 3: Completed, 4:
Request to cancel)
confirmPayEndTime
string(date-time)
false
none
Deadline for payment confirmation
confirmPayTime
string(date-time)
false
none
Deadline for payment confirmation time
confirmPayTimeout
integer(int32)
false
none
If the confirmation payment is overdue. (0: No, 1: Yes)
confirmPayedExpireMinute
integer(int32)
false
none
Expiration time for payment confirmation (in minutes)
createTime
string(date-time)
false
none
Order create time
currencyRate
number
false
none
Exchange rate
currencyTicketSize
string
false
none
Fiat currency decimal precision
expectedPayTime
string(date-time)
false
none
Expected payment time
expectedReleaseTime
string(date-time)
false
none
Expected release time
fiatSymbol
string
false
none
Fiat currency symbol
fiatUnit
string
false
none
Fiat currency: CNY
iconUrl
string
false
none
Asset icon URL
idNumber
string
false
none
Individual ID number with hidden digits
isComplaintAllowed
boolean
false
none
If order still available for filing a complaint (based on
order status)
merchantNo
string
false
none
Merchant number
nickColor
string
false
none
Merchant nickname background color


---

## Page 196

sapi-v7.4.md
2024-05-08
196 / 419
Name
Type
Required
Restrictions
Description
notifyPayEndTime
string(date-time)
false
none
Deadline for making payment
notifyPayTime
string(date-time)
false
none
Deadline for payment notification time
notifyPayedExpireMinute
integer(int32)
false
none
Expiration time for payment notification (in minutes)
onlineStatus
string
false
none
Merchant online status (0: Offline, 1: Online)
orderNumber
string
false
none
Order number
orderStatus
integer(int32)
false
none
Order status (1: Wait for payment, 2: Wait for release, 3:
Appealing, 4: Completed, 6: Cancelled, 7: Cancelled by
system
origin
string
false
none
Origin of the order
payAccount
string
false
none
Payment method account number
payBank
string
false
none
Bank information for bank-based payment methods
payMethods
[OrderPayMethodVo]
false
none
Associated details for the payment methods
paySubBank
string
false
none
Sub-branch information for bank-based payment
methods
payType
string
false
none
Payment method, e.g.: BANK, WECHAT
payee
string
false
none
Payment method payee name
price
number
false
none
Order price
priceTicketSize
string
false
none
Price decimal precision
qrCodePath
string
false
none
QR code for the payment method
remark
string
false
none
Remarks
selectedPayId
integer(int64)
false
none
Selected payment id for order
sellerMobilePhone
string
false
none
Seller mobile number
sellerName
string
false
none
Seller name
sellerNickname
string
false
none
Seller nickname
takerAmount
number
false
none
taker actual deducted/received amount if taker sell:
taker amount = seller deducted amount = (amount +
taker_commission), if taker buy: taker amount = buyer
received amount = (amount - taker_commission)
takerCommission
number
false
none
taker actual commission
takerCommissionRate
number
false
none
taker actual commission rate
totalPrice
number
false
none
Order total price
tradeMethodCommissionRateVoList
[TradeMethodCommissionRateVo]
false
none
Payment method commission rates
tradeType
string
false
none
Order trade type. 0: BUY, 1: SELL
unreadCount
integer(int32)
false
none
Number of unread messages
updateTime
string(date-time)
false
none
Order update time
42.338.1. Enumerated Values
Property
Value
tradeType
BUY
tradeType
SELL
OrderMatchStatsResp
{ 
  "buyerPayedCount": 0, 
  "inAppealCount": 0, 
  "inProcessCount": 0, 
  "tradingCount": 0 
} 
 


---

## Page 197

sapi-v7.4.md
2024-05-08
197 / 419
OrderMatchStatsResp
42.339. Properties
Name
Type
Required
Restrictions
Description
buyerPayedCount
integer(int64)
false
none
Number of paid orders
inAppealCount
integer(int64)
false
none
Number of orders in appealing
inProcessCount
integer(int64)
false
none
Number of in-process orders
tradingCount
integer(int64)
false
none
Number of uncompleted orders
OrderNoReq
{ 
  "orderNumber": "string" 
} 
 
OrderNoReq
42.340. Properties
Name
Type
Required
Restrictions
Description
orderNumber
string
false
none
Order No
OrderOcoResponse
{ 
  "contingencyType": "OCO", 
  "listClientOrderId": "string", 
  "listOrderStatus": "ALL_DONE", 
  "listStatusType": "ALL_DONE", 
  "orderListId": 0, 
  "orderReports": [ 
    { 
      "clientOrderId": "string", 
      "cummulativeQuoteQty": 0, 
      "executedQty": 0, 
      "orderId": 0, 
      "orderListId": 0, 
      "origQty": 0, 
      "price": 0, 
      "selfTradePreventionMode": "string", 
      "side": "BUY", 
      "status": "string", 
      "stopPrice": 0, 
      "symbol": "string", 
      "timeInForce": "FOK", 
      "transactTime": 0, 
      "type": "LIMIT" 
    } 
  ], 
  "orders": [ 
    { 
      "clientOrderId": "string", 
      "code": 0, 
      "confirmedTime": 0, 
      "createTime": 0, 
      "expiryTime": 0, 
      "msg": "string", 
      "orderId": 0, 
      "orderStatus": "string", 
      "price": 0, 
      "quantity": 0, 
      "quoteAsset": "string", 
      "settleTime": 0, 
      "strikePrice": 0, 
      "timeInForce": "string", 
      "type": "string", 
      "underlying": "string" 
    } 
  ], 
  "symbol": "string", 


---

## Page 198

sapi-v7.4.md
2024-05-08
198 / 419
  "transactionTime": 0 
} 
 
OrderOcoResponse
42.341. Properties
Name
Type
Required
Restrictions
Description
contingencyType
string
false
none
none
listClientOrderId
string
false
none
none
listOrderStatus
string
false
none
none
listStatusType
string
false
none
none
orderListId
integer(int64)
false
none
none
orderReports
[OrderReport]
false
none
none
orders
[Order0]
false
none
none
symbol
string
false
none
none
transactionTime
integer(int64)
false
none
none
42.341.1. Enumerated Values
Property
Value
contingencyType
OCO
listOrderStatus
ALL_DONE
listOrderStatus
EXECUTING
listOrderStatus
REJECT
listStatusType
ALL_DONE
listStatusType
EXEC_STARTED
listStatusType
RESPONSE
OrderPayMethodVo
{ 
  "fields": [ 
    { 
      "fieldContentType": "string", 
      "fieldId": "string", 
      "fieldName": "string", 
      "fieldValue": "string", 
      "hintWord": "string", 
      "isCopyable": true, 
      "isRequired": true, 
      "lengthLimit": 0, 
      "restrictionType": 0, 
      "sequence": 0 
    } 
  ], 
  "iconUrlColor": "string", 
  "id": 0, 
  "identifier": "string", 
  "tradeMethodName": "string" 
} 
 
OrderPayMethodVo
42.342. Properties
Name
Type
Required
Restrictions
Description
fields
[PayMethodFieldValue]
false
none
Trade method field list
iconUrlColor
string
false
none
Icon URL with background color


---

## Page 199

sapi-v7.4.md
2024-05-08
199 / 419
Name
Type
Required
Restrictions
Description
id
integer(int64)
false
none
User trade method ID
identifier
string
false
none
Identifier of trade method. Eg: AliPay, Visa
tradeMethodName
string
false
none
Trade method display name
OrderPurchaseResultResp
{ 
  "records": [ 
    { 
      "amount": 0, 
      "id": 0, 
      "optionPrice": 0, 
      "orderId": 0, 
      "symbol": "string", 
      "timestamp": 0 
    } 
  ] 
} 
 
OrderPurchaseResultResp
42.343. Properties
Name
Type
Required
Restrictions
Description
records
[PurchaseRecord]
false
none
none
OrderRateLimitResp
{ 
  "count": 0, 
  "interval": "string", 
  "intervalNum": 0, 
  "limit": 0, 
  "rateLimitType": "string" 
} 
 
OrderRateLimitResp
42.344. Properties
Name
Type
Required
Restrictions
Description
count
integer(int64)
false
none
none
interval
string
false
none
none
intervalNum
integer(int64)
false
none
none
limit
integer(int64)
false
none
none
rateLimitType
string
false
none
none
OrderReport
{ 
  "clientOrderId": "string", 
  "cummulativeQuoteQty": 0, 
  "executedQty": 0, 
  "orderId": 0, 
  "orderListId": 0, 
  "origQty": 0, 
  "price": 0, 
  "selfTradePreventionMode": "string", 
  "side": "BUY", 
  "status": "string", 
  "stopPrice": 0, 
  "symbol": "string", 
  "timeInForce": "FOK", 


---

## Page 200

sapi-v7.4.md
2024-05-08
200 / 419
  "transactTime": 0, 
  "type": "LIMIT" 
} 
 
OrderReport
42.345. Properties
Name
Type
Required
Restrictions
Description
clientOrderId
string
false
none
none
cummulativeQuoteQty
number
false
none
none
executedQty
number
false
none
none
orderId
integer(int64)
false
none
none
orderListId
integer(int64)
false
none
none
origQty
number
false
none
none
price
number
false
none
none
selfTradePreventionMode
string
false
none
none
side
string
false
none
none
status
string
false
none
none
stopPrice
number
false
none
none
symbol
string
false
none
none
timeInForce
string
false
none
none
transactTime
integer(int64)
false
none
none
type
string
false
none
none
42.345.1. Enumerated Values
Property
Value
side
BUY
side
SELL
timeInForce
FOK
timeInForce
GTC
timeInForce
IOC
type
LIMIT
type
LIMIT_MAKER
type
MARKET
type
STOP_LIMIT
type
STOP_LOSS
type
STOP_LOSS_LIMIT
type
TAKE_PROFIT
type
TAKE_PROFIT_LIMIT
OrderReports
{ 
  "clientOrderId": "string", 
  "cummulativeQuoteQty": 0, 
  "executedQty": 0, 
  "orderId": 0, 
  "orderListId": 0, 
  "origClientOrderId": "string", 
  "origQty": "string", 
  "price": "string", 
  "selfTradePreventionMode": "string", 
  "side": "string", 


---

## Page 201

sapi-v7.4.md
2024-05-08
201 / 419
  "status": "string", 
  "stopPrice": "string", 
  "symbol": "string", 
  "timeInForce": "string", 
  "type": "string" 
} 
 
OrderReports
42.346. Properties
Name
Type
Required
Restrictions
Description
clientOrderId
string
false
none
none
cummulativeQuoteQty
number
false
none
none
executedQty
number
false
none
none
orderId
integer(int64)
false
none
none
orderListId
integer(int64)
false
none
none
origClientOrderId
string
false
none
none
origQty
string
false
none
none
price
string
false
none
none
selfTradePreventionMode
string
false
none
none
side
string
false
none
none
status
string
false
none
none
stopPrice
string
false
none
none
symbol
string
false
none
none
timeInForce
string
false
none
none
type
string
false
none
none
OrderResp
{ 
  "clientOrderId": "string", 
  "code": 0, 
  "confirmedTime": 0, 
  "createTime": 0, 
  "expiryTime": 0, 
  "msg": "string", 
  "orderId": 0, 
  "orderStatus": "string", 
  "price": 0, 
  "quantity": 0, 
  "quoteAsset": "string", 
  "settleTime": 0, 
  "strikePrice": 0, 
  "timeInForce": "string", 
  "type": "string", 
  "underlying": "string" 
} 
 
OrderResp
42.347. Properties
Name
Type
Required
Restrictions
Description
clientOrderId
string
false
none
none
code
integer(int32)
false
none
none
confirmedTime
integer(int64)
false
none
none
createTime
integer(int64)
false
none
none
expiryTime
integer(int64)
false
none
none


---

## Page 202

sapi-v7.4.md
2024-05-08
202 / 419
Name
Type
Required
Restrictions
Description
msg
string
false
none
none
orderId
integer(int64)
false
none
none
orderStatus
string
false
none
none
price
number
false
none
none
quantity
number
false
none
none
quoteAsset
string
false
none
none
settleTime
integer(int64)
false
none
none
strikePrice
number
false
none
none
timeInForce
string
false
none
none
type
string
false
none
none
underlying
string
false
none
none
OrderResultResp
{ 
  "clientOrderId": "string", 
  "orderId": 0, 
  "reason": "string", 
  "status": "ACCEPTED", 
  "symbol": "string" 
} 
 
OrderResultResp
42.348. Properties
Name
Type
Required
Restrictions
Description
clientOrderId
string
false
none
none
orderId
integer(int64)
false
none
none
reason
string
false
none
none
status
string
false
none
none
symbol
string
false
none
none
42.348.1. Enumerated Values
Property
Value
status
ACCEPTED
status
CANCELLED
status
CANCELLING
status
CLOSING
status
DUPLICATE_CANCEL
status
ENDED
status
FILLED
status
NO_ORDER
status
OPEN
status
REJECTED
status
UNKNOWN
Orders
{ 
  "clientOrderId": "string", 
  "orderId": 0, 


---

## Page 203

sapi-v7.4.md
2024-05-08
203 / 419
  "symbol": "string" 
} 
 
Orders
42.349. Properties
Name
Type
Required
Restrictions
Description
clientOrderId
string
false
none
none
orderId
integer(int64)
false
none
none
symbol
string
false
none
none
OtcAcceptQuoteResp
{ 
  "baseCoin": "string", 
  "baseCoinAmount": 0, 
  "direction": "string", 
  "feeAmount": "string", 
  "orderId": "string", 
  "quoteCoin": "string", 
  "quoteCoinAmount": 0, 
  "quotePrice": 0, 
  "status": "string" 
} 
 
OtcAcceptQuoteResp
42.350. Properties
Name
Type
Required
Restrictions
Description
baseCoin
string
false
none
baseCoin
baseCoinAmount
number
false
none
baseCoinAmount
direction
string
false
none
买卖⽅向 BUY/SELL
feeAmount
string
false
none
⼿续费
orderId
string
false
none
orderId
quoteCoin
string
false
none
quoteCoin
quoteCoinAmount
number
false
none
quoteCoinAmount
quotePrice
number
false
none
报价价格
status
string
false
none
状态, SUCCESS/FAIL/PROCESS
OtcChannelOrderResp
{ 
  "endTime": 0, 
  "limit": 0, 
  "list": [ 
    { 
      "commissionAmount": 0, 
      "commissionCoin": "string", 
      "commissionTransferred": true, 
      "createTime": 0, 
      "fromAmount": 0, 
      "fromAsset": "string", 
      "inverseRatio": 0, 
      "orderId": 0, 
      "orderStatus": "string", 
      "orderType": "string", 
      "quoteId": "string", 
      "ratio": 0, 
      "side": "string", 
      "toAmount": 0, 
      "toAsset": "string" 
    } 


---

## Page 204

sapi-v7.4.md
2024-05-08
204 / 419
  ], 
  "moreData": true, 
  "size": 0, 
  "startTime": 0 
} 
 
OtcChannelOrderResp
42.351. Properties
Name
Type
Required
Restrictions
Description
endTime
integer(int64)
false
none
none
limit
integer(int32)
false
none
none
list
[OtcSapiTradeOrderResponse]
false
none
none
moreData
boolean
false
none
none
size
integer(int32)
false
none
none
startTime
integer(int64)
false
none
none
OtcChannelQueryResp
{ 
  "completedTime": "string", 
  "inAmount": 0, 
  "inCoin": "string", 
  "outAmount": 0, 
  "outCoin": "string", 
  "quoteId": "string", 
  "side": "string", 
  "status": "string", 
  "symbol": "string" 
} 
 
OtcChannelQueryResp
42.352. Properties
Name
Type
Required
Restrictions
Description
completedTime
string
false
none
none
inAmount
number
false
none
none
inCoin
string
false
none
none
outAmount
number
false
none
none
outCoin
string
false
none
none
quoteId
string
false
none
none
side
string
false
none
none
status
string
false
none
none
symbol
string
false
none
none
OtcCollateralAssetResponse
{ 
  "currency": "string", 
  "details": [ 
    { 
      "userId": 0, 
      "value": 0 
    } 
  ], 
  "totalValue": 0 
} 
 


---

## Page 205

sapi-v7.4.md
2024-05-08
205 / 419
OtcCollateralAssetResponse
42.353. Properties
Name
Type
Required
Restrictions
Description
currency
string
false
none
none
details
[UserAsset]
false
none
none
totalValue
number
false
none
none
OtcGetQuoteResp
{ 
  "baseCoin": "string", 
  "baseCoinAmount": 0, 
  "direction": "string", 
  "expireTime": 0, 
  "payCoinAsset": 0, 
  "quoteCoin": "string", 
  "quoteCoinAmount": 0, 
  "quoteId": "string", 
  "quotePrice": 0, 
  "requestAmount": 0, 
  "requestAmountCoin": "string" 
} 
 
OtcGetQuoteResp
42.354. Properties
Name
Type
Required
Restrictions
Description
baseCoin
string
false
none
baseCoin
baseCoinAmount
number
false
none
baseCoinAmount
direction
string
false
none
买卖⽅向 BUY/SELL
expireTime
integer(int64)
false
none
报价过期时间的时间戳
payCoinAsset
number
false
none
当前⽤户资产
quoteCoin
string
false
none
quoteCoin
quoteCoinAmount
number
false
none
quoteCoinAmount
quoteId
string
false
none
报价ID, 如果quoteId没有，不能进⾏执⾏(⽀付资产不⾜)
quotePrice
number
false
none
报价价格
requestAmount
number
false
none
请求⾦额
requestAmountCoin
string
false
none
请求币种
OtcHistoryResp
{ 
  "baseCoin": "string", 
  "baseCoinAmount": 0, 
  "direction": "string", 
  "orderId": "string", 
  "quoteCoin": "string", 
  "quoteCoinAmount": 0, 
  "quotePrice": 0, 
  "status": "string", 
  "time": "2019-08-24T14:15:22Z" 
} 
 
OtcHistoryResp
42.355. Properties
Name
Type
Required
Restrictions
Description


---

## Page 206

sapi-v7.4.md
2024-05-08
206 / 419
Name
Type
Required
Restrictions
Description
baseCoin
string
false
none
baseCoin
baseCoinAmount
number
false
none
baseCoinAmount
direction
string
false
none
买卖⽅向, BUY/SELL
orderId
string
false
none
orderId
quoteCoin
string
false
none
quoteCoin
quoteCoinAmount
number
false
none
quoteCoinAmount
quotePrice
number
false
none
报价价格
status
string
false
none
状态
time
string(date-time)
false
none
⽇期时间, date(long) 类型
OtcQuerySettleStatusResponse
{ 
  "paying": 0, 
  "payingCoin": "string", 
  "quoteId": "string", 
  "receiving": 0, 
  "receivingCoin": "string", 
  "status": "string" 
} 
 
OtcQuerySettleStatusResponse
42.356. Properties
Name
Type
Required
Restrictions
Description
paying
number
false
none
paying
payingCoin
string
false
none
paying
quoteId
string
false
none
quoteId
receiving
number
false
none
receiving
receivingCoin
string
false
none
receiving
status
string
false
none
status
OtcQueryUserCreditResp
{ 
  "asset": "string", 
  "estimateAssets": [ 
    { 
      "amount": 0, 
      "asset": "string" 
    } 
  ], 
  "totalAmount": 0, 
  "unrealizedLoss": 0, 
  "usedAmount": 0 
} 
 
OtcQueryUserCreditResp
42.357. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
Credit Asset
estimateAssets
[EstimateAsset]
false
none
none
totalAmount
number
false
none
Total credit amount
unrealizedLoss
number
false
none
OTC unrealized loss


---

## Page 207

sapi-v7.4.md
2024-05-08
207 / 419
Name
Type
Required
Restrictions
Description
usedAmount
number
false
none
Used credit amount
OtcQueryUserUnsettleResponse
{ 
  "details": [ 
    { 
      "asset": "string", 
      "netReceive": 0 
    } 
  ] 
} 
 
OtcQueryUserUnsettleResponse
42.358. Properties
Name
Type
Required
Restrictions
Description
details
[UnsettleDetail]
false
none
none
OtcSapiAssetResponse
{ 
  "asset": "string", 
  "fraction": 0 
} 
 
OtcSapiAssetResponse
42.359. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
fraction
integer(int32)
false
none
none
OtcSapiExecuteQuoteResponse
{ 
  "createTime": 0, 
  "orderId": "string", 
  "orderStatus": "string" 
} 
 
OtcSapiExecuteQuoteResponse
42.360. Properties
Name
Type
Required
Restrictions
Description
createTime
integer(int64)
false
none
订单创建时间戳
orderId
string
false
none
orderId
orderStatus
string
false
none
订单状态, PROCESS/ACCEPT_SUCCESS/SUCCESS/FAIL
OtcSapiLimitOrderResp
{ 
  "baseAmount": 0, 
  "baseAsset": "string", 
  "createTime": 0, 
  "expiredTimestamp": 0, 
  "expiredType": "string", 
  "limitPrice": 0, 


---

## Page 208

sapi-v7.4.md
2024-05-08
208 / 419
  "orderId": 0, 
  "orderStatus": "string", 
  "quoteAmount": 0, 
  "quoteAsset": "string", 
  "quoteId": "string", 
  "side": "string", 
  "walletType": "string" 
} 
 
OtcSapiLimitOrderResp
42.361. Properties
Name
Type
Required
Restrictions
Description
baseAmount
number
false
none
base asset amount
baseAsset
string
false
none
baseAsset
createTime
integer(int64)
false
none
create timestamp
expiredTimestamp
integer(int64)
false
none
limit order expired timestamp
expiredType
string
false
none
expired type
limitPrice
number
false
none
base:quote price
orderId
integer(int64)
false
none
order id
orderStatus
string
false
none
order status: PROCESS/SUCCESS/FAIL
quoteAmount
number
false
none
quote asset amount
quoteAsset
string
false
none
quote asset amount
quoteId
string
false
none
quote ID
side
string
false
none
trade side: BUY or SELL
walletType
string
false
none
wallet type
OtcSapiSymbolInfo
{ 
  "baseAsset": "string", 
  "baseAssetMaxAmount": 0, 
  "baseAssetMinAmount": 0, 
  "quoteAsset": "string", 
  "quoteAssetMaxAmount": 0, 
  "quoteAssetMinAmount": 0, 
  "symbol": "string" 
} 
 
OtcSapiSymbolInfo
42.362. Properties
Name
Type
Required
Restrictions
Description
baseAsset
string
false
none
none
baseAssetMaxAmount
number
false
none
none
baseAssetMinAmount
number
false
none
none
quoteAsset
string
false
none
none
quoteAssetMaxAmount
number
false
none
none
quoteAssetMinAmount
number
false
none
none
symbol
string
false
none
none
OtcSapiTradeOrderResponse
{ 
  "commissionAmount": 0, 
  "commissionCoin": "string", 


---

## Page 209

sapi-v7.4.md
2024-05-08
209 / 419
  "commissionTransferred": true, 
  "createTime": 0, 
  "fromAmount": 0, 
  "fromAsset": "string", 
  "inverseRatio": 0, 
  "orderId": 0, 
  "orderStatus": "string", 
  "orderType": "string", 
  "quoteId": "string", 
  "ratio": 0, 
  "side": "string", 
  "toAmount": 0, 
  "toAsset": "string" 
} 
 
OtcSapiTradeOrderResponse
42.363. Properties
Name
Type
Required
Restrictions
Description
commissionAmount
number
false
none
none
commissionCoin
string
false
none
commission relative
commissionTransferred
boolean
false
none
none
createTime
integer(int64)
false
none
订单创建时间戳
fromAmount
number
false
none
fromAsset⾦额
fromAsset
string
false
none
fromAsset
inverseRatio
number
false
none
to:from报价
orderId
integer(int64)
false
none
订单号
orderStatus
string
false
none
订单⽤户状态:PROCESS/SUCCESS/FAIL
orderType
string
false
none
order type: MARKET LIMIT
quoteId
string
false
none
报价ID
ratio
number
false
none
from:to报价
side
string
false
none
trade side: BUY or SELL
toAmount
number
false
none
toAsset⾦额
toAsset
string
false
none
toAsset
OtcSymbolResponse
{ 
  "symbol": "string" 
} 
 
OtcSymbolResponse
42.364. Properties
Name
Type
Required
Restrictions
Description
symbol
string
false
none
币对
OtcSymbolSelector
{ 
  "base": "string", 
  "baseMax": 0, 
  "baseMin": 0, 
  "quote": "string", 
  "quoteMax": 0, 
  "quoteMin": 0, 
  "trade": "string" 
} 
 


---

## Page 210

sapi-v7.4.md
2024-05-08
210 / 419
OtcSymbolSelector
42.365. Properties
Name
Type
Required
Restrictions
Description
base
string
false
none
none
baseMax
number
false
none
none
baseMin
number
false
none
none
quote
string
false
none
none
quoteMax
number
false
none
none
quoteMin
number
false
none
none
trade
string
false
none
none
PairLimitResponse
{ 
  "base": "string", 
  "baseMax": 0, 
  "baseMin": 0, 
  "quote": "string", 
  "quoteMax": 0, 
  "quoteMin": 0 
} 
 
PairLimitResponse
42.366. Properties
Name
Type
Required
Restrictions
Description
base
string
false
none
none
baseMax
number
false
none
none
baseMin
number
false
none
none
quote
string
false
none
none
quoteMax
number
false
none
none
quoteMin
number
false
none
none
PartnerTransferResp
{ 
  "orderId": "string", 
  "outStatus": "APPLY", 
  "status": "APPLY" 
} 
 
PartnerTransferResp
42.367. Properties
Name
Type
Required
Restrictions
Description
orderId
string
false
none
none
outStatus
string
false
none
第三⽅转⼊转出状态
status
string
false
none
币安转⼊转出状态
42.367.1. Enumerated Values
Property
Value
outStatus
APPLY


---

## Page 211

sapi-v7.4.md
2024-05-08
211 / 419
Property
Value
outStatus
CANCELED
outStatus
FAILURE
outStatus
PENDING
outStatus
SUCCESS
status
APPLY
status
CANCELED
status
FAILURE
status
PENDING
status
SUCCESS
PayMethodDto
{ 
  "iconUrlColor": "string", 
  "id": 0, 
  "identifier": "string", 
  "payAccount": "string", 
  "payBank": "string", 
  "payMethodId": "string", 
  "paySubBank": "string", 
  "payType": "string", 
  "tradeMethodBgColor": "string", 
  "tradeMethodName": "string", 
  "tradeMethodShortName": "string" 
} 
 
PayMethodDto
42.368. Properties
Name
Type
Required
Restrictions
Description
iconUrlColor
string
false
none
[new]交易⽅式图标
id
integer(int64)
false
none
none
identifier
string
false
none
[new]交易⽅式识别符，形如'wechat
payAccount
string
false
none
none
payBank
string
false
none
none
payMethodId
string
false
none
⽀付⽅式ID String
paySubBank
string
false
none
none
payType
string
false
none
none
tradeMethodBgColor
string
false
none
交易⽅式背景颜⾊
tradeMethodName
string
false
none
[new]交易⽅式名称
tradeMethodShortName
string
false
none
[new]交易⽅式缩写名称
PayMethodFieldValue
{ 
  "fieldContentType": "string", 
  "fieldId": "string", 
  "fieldName": "string", 
  "fieldValue": "string", 
  "hintWord": "string", 
  "isCopyable": true, 
  "isRequired": true, 
  "lengthLimit": 0, 
  "restrictionType": 0, 
  "sequence": 0 
} 
 


---

## Page 212

sapi-v7.4.md
2024-05-08
212 / 419
PayMethodFieldValue
42.369. Properties
Name
Type
Required
Restrictions
Description
fieldContentType
string
false
none
字段类型：payee姓名 single_text单⾏⽂本框 multi_text多⾏⽂本框 qr_code⼆维码
pay_account账号 bank银⾏名称 sub_bank分⾏名称
fieldId
string
false
none
field定义id
fieldName
string
false
none
field名称
fieldValue
string
false
none
Value of trade method field
hintWord
string
false
none
提示语
isCopyable
boolean
false
none
是否可以拷⻉, false否，true是
isRequired
boolean
false
none
是否必填，false否，true是
lengthLimit
integer(int32)
false
none
⻓度限制字符数
restrictionType
integer(int32)
false
none
格式限制，0不限制，1仅数字， 2数字+字⺟
sequence
integer(int32)
false
none
字段顺序
PayMethodResp
{ 
  "advCount": 0, 
  "createTime": "2019-08-24T14:15:22Z", 
  "currentPayAmount": 0, 
  "fieldList": [ 
    { 
      "createTime": "2019-08-24T14:15:22Z", 
      "errorKey": "string", 
      "errorWord": "string", 
      "fieldContentType": "string", 
      "fieldId": "string", 
      "fieldName": "string", 
      "fieldTitle": "string", 
      "fieldTitleKey": "string", 
      "fieldValue": "string", 
      "hintKey": "string", 
      "hintWord": "string", 
      "id": 0, 
      "isCopyable": 0, 
      "isDisplay": 0, 
      "isEncrypt": 0, 
      "isRequired": 0, 
      "lengthLimit": 0, 
      "restrictionType": 0, 
      "sequence": 0, 
      "status": 0, 
      "updateTime": "2019-08-24T14:15:22Z" 
    } 
  ], 
  "forbidReason": "string", 
  "id": 0, 
  "isRemoved": 0, 
  "mainUserId": 0, 
  "payAccount": "string", 
  "payBank": "string", 
  "payLimit": 0, 
  "payLimitUnit": "string", 
  "payStatus": "ACTIVE", 
  "paySubBank": "string", 
  "payType": "ALIPAY", 
  "payee": "string", 
  "qrCodePath": "string", 
  "tradeMethod": { 
    "bgColor": "string", 
    "chatNeed": 0, 
    "createTime": "2019-08-24T14:15:22Z", 
    "iconUrlColor": "string", 
    "iconUrlGray": "string", 
    "id": 0, 
    "identifier": "string", 
    "isOnline": 0, 
    "isRecommended": 0, 


---

## Page 213

sapi-v7.4.md
2024-05-08
213 / 419
    "isVisible": 0, 
    "multiAllow": 0, 
    "name": "string", 
    "nameKey": "string", 
    "remark": "string", 
    "risk": "string", 
    "riskKey": "string", 
    "riskLevel": 0, 
    "sequence": 0, 
    "shortName": "string", 
    "shortNameKey": "string", 
    "tradeMethodCode": 0, 
    "typeCode": "string", 
    "typeName": "string", 
    "updateTime": "2019-08-24T14:15:22Z" 
  }, 
  "tradeMethodIdentifier": "string", 
  "updateTime": "2019-08-24T14:15:22Z", 
  "userId": 0 
} 
 
PayMethodResp
42.370. Properties
Name
Type
Required
Restrictions
Description
advCount
integer(int32)
false
none
none
createTime
string(date-time)
false
none
none
currentPayAmount
number
false
none
none
fieldList
[_field]
false
none
⽀付⽅式字段内容
forbidReason
string
false
none
none
id
integer(int64)
false
none
none
isRemoved
integer(int32)
false
none
none
mainUserId
integer(int64)
false
none
none
payAccount
string
false
none
none
payBank
string
false
none
none
payLimit
number
false
none
none
payLimitUnit
string
false
none
none
payStatus
string
false
none
none
paySubBank
string
false
none
none
payType
string
false
none
none
payee
string
false
none
none
qrCodePath
string
false
none
none
tradeMethod
_
false
none
none
tradeMethodIdentifier
string
false
none
none
updateTime
string(date-time)
false
none
none
userId
integer(int64)
false
none
none
42.370.1. Enumerated Values
Property
Value
payStatus
ACTIVE
payStatus
FORBID
payStatus
INACTIVE
payType
ALIPAY
payType
BANK
payType
QIWI


---

## Page 214

sapi-v7.4.md
2024-05-08
214 / 419
Property
Value
payType
WECHAT
PayMethodVO
{ 
  "advCount": 0, 
  "createTime": "2019-08-24T14:15:22Z", 
  "currentPayAmount": 0, 
  "fieldList": [ 
    { 
      "createTime": "2019-08-24T14:15:22Z", 
      "errorKey": "string", 
      "errorWord": "string", 
      "fieldContentType": "string", 
      "fieldId": "string", 
      "fieldName": "string", 
      "fieldTitle": "string", 
      "fieldTitleKey": "string", 
      "fieldValue": "string", 
      "hintKey": "string", 
      "hintWord": "string", 
      "id": 0, 
      "isCopyable": 0, 
      "isDisplay": 0, 
      "isEncrypt": 0, 
      "isRequired": 0, 
      "lengthLimit": 0, 
      "restrictionType": 0, 
      "sequence": 0, 
      "status": 0, 
      "updateTime": "2019-08-24T14:15:22Z" 
    } 
  ], 
  "iconUrlColor": "string", 
  "id": 0, 
  "isRemoved": 0, 
  "mainUserId": 0, 
  "online": true, 
  "payLimit": 0, 
  "payLimitUnit": "string", 
  "payStatus": "ACTIVE", 
  "tradeMethodBgColor": "string", 
  "tradeMethodIdentifier": "string", 
  "tradeMethodName": "string", 
  "tradeMethodRisk": "string", 
  "tradeMethodShortName": "string", 
  "updateTime": "2019-08-24T14:15:22Z", 
  "userId": 0 
} 
 
PayMethodVO
42.371. Properties
Name
Type
Required
Restrictions
Description
advCount
integer(int32)
false
none
none
createTime
string(date-time)
false
none
none
currentPayAmount
number
false
none
none
fieldList
[_field]
false
none
none
iconUrlColor
string
false
none
none
id
integer(int64)
false
none
none
isRemoved
integer(int32)
false
none
none
mainUserId
integer(int64)
false
none
none
online
boolean
false
none
none
payLimit
number
false
none
none
payLimitUnit
string
false
none
none


---

## Page 215

sapi-v7.4.md
2024-05-08
215 / 419
Name
Type
Required
Restrictions
Description
payStatus
string
false
none
none
tradeMethodBgColor
string
false
none
none
tradeMethodIdentifier
string
false
none
none
tradeMethodName
string
false
none
none
tradeMethodRisk
string
false
none
none
tradeMethodShortName
string
false
none
none
updateTime
string(date-time)
false
none
none
userId
integer(int64)
false
none
none
42.371.1. Enumerated Values
Property
Value
payStatus
ACTIVE
payStatus
FORBID
payStatus
INACTIVE
PersonalLeftQuotaResp
{ 
  "leftPersonalQuota": 0 
} 
 
PersonalLeftQuotaResp
42.372. Properties
Name
Type
Required
Restrictions
Description
leftPersonalQuota
number
false
none
none
PlaceLimitOrderResp
{ 
  "orderId": 0, 
  "status": "string" 
} 
 
PlaceLimitOrderResp
42.373. Properties
Name
Type
Required
Restrictions
Description
orderId
integer(int64)
false
none
none
status
string
false
none
none
PlaceOcoOrderResp
{ 
  "contingencyType": "string", 
  "isIsolated": true, 
  "listClientOrderId": "string", 
  "listOrderStatus": "string", 
  "listStatusType": "string", 
  "marginBuyBorrowAmount": 0, 
  "marginBuyBorrowAsset": "string", 
  "orderListId": 0, 
  "orderReports": [ 
    { 
      "clientOrderId": "string", 
      "cummulativeQuoteQty": 0, 


---

## Page 216

sapi-v7.4.md
2024-05-08
216 / 419
      "executedQty": 0, 
      "orderId": 0, 
      "orderListId": 0, 
      "origClientOrderId": "string", 
      "origQty": "string", 
      "price": "string", 
      "selfTradePreventionMode": "string", 
      "side": "string", 
      "status": "string", 
      "stopPrice": "string", 
      "symbol": "string", 
      "timeInForce": "string", 
      "type": "string" 
    } 
  ], 
  "orders": [ 
    { 
      "clientOrderId": "string", 
      "orderId": 0, 
      "symbol": "string" 
    } 
  ], 
  "symbol": "string", 
  "transactionTime": 0 
} 
 
PlaceOcoOrderResp
42.374. Properties
Name
Type
Required
Restrictions
Description
contingencyType
string
false
none
none
isIsolated
boolean
false
none
none
listClientOrderId
string
false
none
none
listOrderStatus
string
false
none
none
listStatusType
string
false
none
none
marginBuyBorrowAmount
number
false
none
none
marginBuyBorrowAsset
string
false
none
none
orderListId
integer(int64)
false
none
none
orderReports
[OrderReports]
false
none
none
orders
[Orders]
false
none
none
symbol
string
false
none
none
transactionTime
integer(int64)
false
none
none
PlaceOrderResp
{ 
  "clientOrderId": "string", 
  "cummulativeQuoteQty": 0, 
  "executedQty": 0, 
  "fills": [ 
    { 
      "commission": 0, 
      "commissionAsset": "string", 
      "price": 0, 
      "qty": 0, 
      "tradeId": 0 
    } 
  ], 
  "isIsolated": true, 
  "marginBuyBorrowAmount": 0, 
  "marginBuyBorrowAsset": "string", 
  "orderId": 0, 
  "orderOcoResponse": { 
    "contingencyType": "OCO", 
    "listClientOrderId": "string", 
    "listOrderStatus": "ALL_DONE", 
    "listStatusType": "ALL_DONE", 


---

## Page 217

sapi-v7.4.md
2024-05-08
217 / 419
    "orderListId": 0, 
    "orderReports": [ 
      { 
        "clientOrderId": "string", 
        "cummulativeQuoteQty": 0, 
        "executedQty": 0, 
        "orderId": 0, 
        "orderListId": 0, 
        "origQty": 0, 
        "price": 0, 
        "selfTradePreventionMode": "string", 
        "side": "BUY", 
        "status": "string", 
        "stopPrice": 0, 
        "symbol": "string", 
        "timeInForce": "FOK", 
        "transactTime": 0, 
        "type": "LIMIT" 
      } 
    ], 
    "orders": [ 
      { 
        "clientOrderId": "string", 
        "code": 0, 
        "confirmedTime": 0, 
        "createTime": 0, 
        "expiryTime": 0, 
        "msg": "string", 
        "orderId": 0, 
        "orderStatus": "string", 
        "price": 0, 
        "quantity": 0, 
        "quoteAsset": "string", 
        "settleTime": 0, 
        "strikePrice": 0, 
        "timeInForce": "string", 
        "type": "string", 
        "underlying": "string" 
      } 
    ], 
    "symbol": "string", 
    "transactionTime": 0 
  }, 
  "origQty": 0, 
  "price": 0, 
  "selfTradePreventionMode": "string", 
  "side": "string", 
  "status": "string", 
  "symbol": "string", 
  "timeInForce": "string", 
  "transactTime": 0, 
  "type": "string" 
} 
 
PlaceOrderResp
42.375. Properties
Name
Type
Required
Restrictions
Description
clientOrderId
string
false
none
none
cummulativeQuoteQty
number
false
none
none
executedQty
number
false
none
none
fills
[OrderFill]
false
none
none
isIsolated
boolean
false
none
none
marginBuyBorrowAmount
number
false
none
none
marginBuyBorrowAsset
string
false
none
none
orderId
integer(int64)
false
none
none
orderOcoResponse
OrderOcoResponse
false
none
none
origQty
number
false
none
none
price
number
false
none
none


---

## Page 218

sapi-v7.4.md
2024-05-08
218 / 419
Name
Type
Required
Restrictions
Description
selfTradePreventionMode
string
false
none
none
side
string
false
none
none
status
string
false
none
none
symbol
string
false
none
none
timeInForce
string
false
none
none
transactTime
integer(int64)
false
none
none
type
string
false
none
none
PoolConfigureSapiDto
{ 
  "assetConfigure": { 
    "property1": { 
      "maxAdd": 0, 
      "maxSwap": 0, 
      "minAdd": 0, 
      "minSwap": 0 
    }, 
    "property2": { 
      "maxAdd": 0, 
      "maxSwap": 0, 
      "minAdd": 0, 
      "minSwap": 0 
    } 
  }, 
  "liquidity": { 
    "constantA": 0, 
    "minRedeemShare": 0, 
    "slippageTolerance": 0 
  }, 
  "poolId": 0, 
  "poolName": "string", 
  "swapRewardsRatio": 0, 
  "updateTime": 0 
} 
 
PoolConfigureSapiDto
42.376. Properties
Name
Type
Required
Restrictions
Description
assetConfigure
object
false
none
none
» additionalProperties
AssetConfig
false
none
none
liquidity
Liquidity
false
none
none
poolId
integer(int64)
false
none
none
poolName
string
false
none
none
swapRewardsRatio
number
false
none
none
updateTime
integer(int64)
false
none
none
PoolVolume
{ 
  "baseAsset": "string", 
  "baseVol": "string", 
  "poolId": "string", 
  "poolName": "string", 
  "quoteAsset": "string", 
  "quoteVol": "string" 
} 
 
PoolVolume


---

## Page 219

sapi-v7.4.md
2024-05-08
219 / 419
42.377. Properties
Name
Type
Required
Restrictions
Description
baseAsset
string
false
none
none
baseVol
string
false
none
none
poolId
string
false
none
none
poolName
string
false
none
none
quoteAsset
string
false
none
none
quoteVol
string
false
none
none
Position
{ 
  "accrualDays": 0, 
  "amount": 0, 
  "apy": 0, 
  "asset": "string", 
  "autoSubscribe": true, 
  "canFastRedemption": true, 
  "canReStake": true, 
  "canRedeemEarly": true, 
  "deliverDate": 0, 
  "duration": 0, 
  "estExtraRewardAmt": 0, 
  "extraRewardAPR": 0, 
  "extraRewardAsset": "string", 
  "nextPay": 0, 
  "nextPayDate": 0, 
  "partialAmtDeliverDate": 0, 
  "payPeriod": 0, 
  "positionId": 0, 
  "projectId": "string", 
  "purchaseTime": 0, 
  "reStakeInfo": { 
    "estRewards": 0, 
    "reStakeAmount": 0, 
    "reStakeApr": 0, 
    "reStakeDeliverDate": 0, 
    "reStakeDuration": 0, 
    "reStakeRate": 0, 
    "reStakeRewardsEndDate": 0 
  }, 
  "redeemAmountEarly": 0, 
  "redeemPeriod": 0, 
  "redeemTo": "string", 
  "redeemingAmt": 0, 
  "rewardAmt": 0, 
  "rewardAsset": "string", 
  "rewardsEndDate": 0, 
  "status": "string", 
  "type": "string" 
} 
 
Position
42.378. Properties
Name
Type
Required
Restrictions
Description
accrualDays
integer(int32)
false
none
none
amount
number
false
none
none
apy
number
false
none
none
asset
string
false
none
none
autoSubscribe
boolean
false
none
none
canFastRedemption
boolean
false
none
none
canReStake
boolean
false
none
none
canRedeemEarly
boolean
false
none
none


---

## Page 220

sapi-v7.4.md
2024-05-08
220 / 419
Name
Type
Required
Restrictions
Description
deliverDate
integer(int64)
false
none
none
duration
integer(int32)
false
none
none
estExtraRewardAmt
number
false
none
none
extraRewardAPR
number
false
none
none
extraRewardAsset
string
false
none
none
nextPay
number
false
none
none
nextPayDate
integer(int64)
false
none
none
partialAmtDeliverDate
integer(int64)
false
none
none
payPeriod
integer(int32)
false
none
none
positionId
integer(int64)
false
none
none
projectId
string
false
none
none
purchaseTime
integer(int64)
false
none
none
reStakeInfo
ReStakeInfo
false
none
none
redeemAmountEarly
number
false
none
none
redeemPeriod
integer(int32)
false
none
none
redeemTo
string
false
none
none
redeemingAmt
number
false
none
none
rewardAmt
number
false
none
none
rewardAsset
string
false
none
none
rewardsEndDate
integer(int64)
false
none
none
status
string
false
none
none
type
string
false
none
none
PositionResp
{ 
  "accrualDays": 0, 
  "amount": 0, 
  "apy": 0, 
  "asset": "string", 
  "canFastRedemption": true, 
  "canReStake": true, 
  "canRedeemEarly": true, 
  "deliverDate": 0, 
  "duration": 0, 
  "estExtraRewardAmt": 0, 
  "extraRewardAPY": 0, 
  "extraRewardAsset": "string", 
  "interestEndDate": 0, 
  "nextInterestPay": 0, 
  "nextInterestPayDate": 0, 
  "partialAmtDeliverDate": 0, 
  "payInterestPeriod": 0, 
  "positionId": 0, 
  "productId": "string", 
  "purchaseTime": 0, 
  "redeemAmountEarly": 0, 
  "redeemPeriod": 0, 
  "redeemingAmt": 0, 
  "renewable": true, 
  "rewardAmt": 0, 
  "rewardAsset": "string", 
  "status": "string", 
  "type": "string" 
} 
 
PositionResp
42.379. Properties


---

## Page 221

sapi-v7.4.md
2024-05-08
221 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
accrualDays
integer(int32)
false
none
none
amount
number
false
none
none
apy
number
false
none
none
asset
string
false
none
none
canFastRedemption
boolean
false
none
none
canReStake
boolean
false
none
none
canRedeemEarly
boolean
false
none
none
deliverDate
integer(int64)
false
none
none
duration
integer(int32)
false
none
none
estExtraRewardAmt
number
false
none
none
extraRewardAPY
number
false
none
none
extraRewardAsset
string
false
none
none
interestEndDate
integer(int64)
false
none
none
nextInterestPay
number
false
none
none
nextInterestPayDate
integer(int64)
false
none
none
partialAmtDeliverDate
integer(int64)
false
none
none
payInterestPeriod
integer(int32)
false
none
none
positionId
integer(int64)
false
none
none
productId
string
false
none
none
purchaseTime
integer(int64)
false
none
none
redeemAmountEarly
number
false
none
none
redeemPeriod
integer(int32)
false
none
none
redeemingAmt
number
false
none
none
renewable
boolean
false
none
none
rewardAmt
number
false
none
none
rewardAsset
string
false
none
none
status
string
false
none
none
type
string
false
none
none
PreviewResp
{ 
  "apr": 0, 
  "deliverDate": 0, 
  "estExtraRewardAmt": 0, 
  "estReward": 0, 
  "extraRewardAPR": 0, 
  "extraRewardAsset": "string", 
  "interestBeginDate": 0, 
  "interestEndDate": 0, 
  "nextInterestPayDate": 0, 
  "payInterestPeriod": 0, 
  "redeemPeriod": 0 
} 
 
PreviewResp
42.380. Properties
Name
Type
Required
Restrictions
Description
apr
number
false
none
none
deliverDate
integer(int64)
false
none
none


---

## Page 222

sapi-v7.4.md
2024-05-08
222 / 419
Name
Type
Required
Restrictions
Description
estExtraRewardAmt
number
false
none
none
estReward
number
false
none
none
extraRewardAPR
number
false
none
none
extraRewardAsset
string
false
none
none
interestBeginDate
integer(int64)
false
none
none
interestEndDate
integer(int64)
false
none
none
nextInterestPayDate
integer(int64)
false
none
none
payInterestPeriod
integer(int32)
false
none
none
redeemPeriod
integer(int32)
false
none
none
Price
{ 
  "fixingPrice": 0, 
  "fixingTime": 0, 
  "fromAsset": "string", 
  "toAsset": "string" 
} 
 
Price
42.381. Properties
Name
Type
Required
Restrictions
Description
fixingPrice
number
false
none
none
fixingTime
integer(int64)
false
none
none
fromAsset
string
false
none
none
toAsset
string
false
none
none
PriceIndexResp
{ 
  "calcTime": 0, 
  "price": 0, 
  "symbol": "string" 
} 
 
PriceIndexResp
42.382. Properties
Name
Type
Required
Restrictions
Description
calcTime
integer(int64)
false
none
none
price
number
false
none
none
symbol
string
false
none
none
PriceIndexResponse
{ 
  "asset": "string", 
  "assetIndexPrice": 0, 
  "time": 0 
} 
 
PriceIndexResponse


---

## Page 223

sapi-v7.4.md
2024-05-08
223 / 419
42.383. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
assetIndexPrice
number
false
none
none
time
integer(int64)
false
none
none
ProMerchantVo
{ 
  "merchantDescription": "string", 
  "merchantLogo": "string" 
} 
 
ProMerchantVo
42.384. Properties
Name
Type
Required
Restrictions
Description
merchantDescription
string
false
none
商户描述
merchantLogo
string
false
none
商户logo
ProductListResp
{ 
  "detail": { 
    "apy": 0, 
    "asset": "string", 
    "duration": 0, 
    "extraRewardAsset": "string", 
    "extraRewardsAPY": 0, 
    "isSoldOut": true, 
    "project": "string", 
    "renewable": true, 
    "rewardAsset": "string", 
    "status": "string", 
    "subscriptionStartTime": 0 
  }, 
  "projectId": "string", 
  "quota": { 
    "minimum": 0, 
    "quotaPerOrder": 0, 
    "totalPersonalQuota": 0 
  } 
} 
 
ProductListResp
42.385. Properties
Name
Type
Required
Restrictions
Description
detail
ProjectDetail
false
none
none
projectId
string
false
none
none
quota
ProjectQuota
false
none
none
Project
{ 
  "detail": { 
    "apr": 0, 
    "asset": "string", 
    "canPurchase": true, 
    "duration": 0, 
    "extraRewardAPR": 0, 
    "extraRewardAsset": "string", 


---

## Page 224

sapi-v7.4.md
2024-05-08
224 / 419
    "isSoldOut": true, 
    "renewable": true, 
    "rewardAsset": "string", 
    "status": "string", 
    "subscriptionStartTime": 0 
  }, 
  "projectId": "string", 
  "quota": { 
    "minimum": 0, 
    "totalPersonalQuota": 0 
  } 
} 
 
Project
42.386. Properties
Name
Type
Required
Restrictions
Description
detail
Detail
false
none
none
projectId
string
false
none
none
quota
Quota
false
none
none
ProjectDetail
{ 
  "apy": 0, 
  "asset": "string", 
  "duration": 0, 
  "extraRewardAsset": "string", 
  "extraRewardsAPY": 0, 
  "isSoldOut": true, 
  "project": "string", 
  "renewable": true, 
  "rewardAsset": "string", 
  "status": "string", 
  "subscriptionStartTime": 0 
} 
 
ProjectDetail
42.387. Properties
Name
Type
Required
Restrictions
Description
apy
number
false
none
none
asset
string
false
none
none
duration
integer(int32)
false
none
none
extraRewardAsset
string
false
none
none
extraRewardsAPY
number
false
none
none
isSoldOut
boolean
false
none
none
project
string
false
none
none
renewable
boolean
false
none
none
rewardAsset
string
false
none
none
status
string
false
none
none
subscriptionStartTime
integer(int64)
false
none
none
ProjectPositionResp
{ 
  "asset": "string", 
  "canTransfer": true, 
  "createTimestamp": 0, 
  "duration": 0, 


---

## Page 225

sapi-v7.4.md
2024-05-08
225 / 419
  "endTime": 0, 
  "interest": 0, 
  "interestRate": 0, 
  "lot": 0, 
  "positionId": 0, 
  "principal": 0, 
  "projectId": "string", 
  "projectName": "string", 
  "purchaseTime": 0, 
  "redeemDate": "string", 
  "startTime": 0, 
  "status": "HOLDING", 
  "type": "CUSTOMIZED_FIXED" 
} 
 
ProjectPositionResp
42.388. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
币种
canTransfer
boolean
false
none
是否可以定转活
createTimestamp
integer(int64)
false
none
持仓开始时间
duration
integer(int32)
false
none
有效期， 天
endTime
integer(int64)
false
none
计息结束时间
interest
number
false
none
利息
interestRate
number
false
none
预期收益率，仅供展示⽤
lot
integer(int64)
false
none
⼿数
positionId
integer(int64)
false
none
持仓id
principal
number
false
none
持仓量
projectId
string
false
none
项⽬id
projectName
string
false
none
产品名称
purchaseTime
integer(int64)
false
none
申购时间
redeemDate
string
false
none
赎回时间
startTime
integer(int64)
false
none
项⽬开始时间/记息时间
status
string
false
none
1: 持仓中 2: 已赎回
type
string
false
none
持仓类型
42.388.1. Enumerated Values
Property
Value
status
HOLDING
status
REDEEMED
type
CUSTOMIZED_FIXED
type
DAILY
type
EXPERIENCE_COUPON
type
REGULAR
type
SUPER_MINING
ProjectQuota
{ 
  "minimum": 0, 
  "quotaPerOrder": 0, 
  "totalPersonalQuota": 0 
} 
 


---

## Page 226

sapi-v7.4.md
2024-05-08
226 / 419
ProjectQuota
42.389. Properties
Name
Type
Required
Restrictions
Description
minimum
number
false
none
none
quotaPerOrder
number
false
none
none
totalPersonalQuota
number
false
none
none
ProjectResp
{ 
  "rows": [ 
    { 
      "detail": { 
        "apr": 0, 
        "asset": "string", 
        "canPurchase": true, 
        "duration": 0, 
        "extraRewardAPR": 0, 
        "extraRewardAsset": "string", 
        "isSoldOut": true, 
        "renewable": true, 
        "rewardAsset": "string", 
        "status": "string", 
        "subscriptionStartTime": 0 
      }, 
      "projectId": "string", 
      "quota": { 
        "minimum": 0, 
        "totalPersonalQuota": 0 
      } 
    } 
  ], 
  "total": 0 
} 
 
ProjectResp
42.390. Properties
Name
Type
Required
Restrictions
Description
rows
[Project]
false
none
none
total
integer(int64)
false
none
none
ProjectsResp
{ 
  "asset": "string", 
  "displayPriority": 0, 
  "duration": 0, 
  "interestPerLot": 0, 
  "interestRate": 0, 
  "lotSize": 0, 
  "lotsLowLimit": 0, 
  "lotsPurchased": 0, 
  "lotsUpLimit": 0, 
  "maxLotsPerUser": 0, 
  "needKyc": true, 
  "projectId": "string", 
  "projectName": "string", 
  "status": "CREATED", 
  "type": "CUSTOMIZED_FIXED", 
  "withAreaLimitation": true, 
  "withWhiteList": true 
} 
 
ProjectsResp


---

## Page 227

sapi-v7.4.md
2024-05-08
227 / 419
42.391. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
displayPriority
integer(int32)
false
none
none
duration
integer(int32)
false
none
none
interestPerLot
number
false
none
none
interestRate
number
false
none
none
lotSize
number
false
none
none
lotsLowLimit
integer(int64)
false
none
none
lotsPurchased
integer(int64)
false
none
none
lotsUpLimit
integer(int64)
false
none
none
maxLotsPerUser
integer(int64)
false
none
none
needKyc
boolean
false
none
none
projectId
string
false
none
none
projectName
string
false
none
none
status
string
false
none
none
type
string
false
none
none
withAreaLimitation
boolean
false
none
none
withWhiteList
boolean
false
none
none
42.391.1. Enumerated Values
Property
Value
status
CREATED
status
DEDUCTED
status
PREHEATING
status
PRE_REDEMPTION
status
PULLED_BACK
status
PURCHASED
status
PURCHASING
status
REDEEMED
status
RUNNING
type
CUSTOMIZED_FIXED
type
DAILY
type
EXPERIENCE_COUPON
type
REGULAR
type
SUPER_MINING
PurchaseIdResp
{ 
  "clientPurchaseId": "string", 
  "purchaseId": 0 
} 
 
PurchaseIdResp
42.392. Properties
Name
Type
Required
Restrictions
Description
clientPurchaseId
string
false
none
none


---

## Page 228

sapi-v7.4.md
2024-05-08
228 / 419
Name
Type
Required
Restrictions
Description
purchaseId
integer(int64)
false
none
none
PurchaseRecord
{ 
  "amount": 0, 
  "id": 0, 
  "optionPrice": 0, 
  "orderId": 0, 
  "symbol": "string", 
  "timestamp": 0 
} 
 
PurchaseRecord
42.393. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
id
integer(int64)
false
none
none
optionPrice
number
false
none
none
orderId
integer(int64)
false
none
none
symbol
string
false
none
none
timestamp
integer(int64)
false
none
none
PurchaseRecordUnionDisplayResp
{ 
  "amount": 0, 
  "asset": "string", 
  "clientPurchaseId": "string", 
  "createTime": 0, 
  "lendingType": "CUSTOMIZED_FIXED", 
  "lot": 0, 
  "productName": "string", 
  "purchaseId": 0, 
  "status": "FAILED" 
} 
 
PurchaseRecordUnionDisplayResp
42.394. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
⾦额
asset
string
false
none
币种
clientPurchaseId
string
false
none
clientPurchaseId
createTime
integer(int64)
false
none
申购时间
lendingType
string
false
none
活期 or 定期
lot
integer(int64)
false
none
⼿数 ： 定期
productName
string
false
none
产品名
purchaseId
integer(int64)
false
none
申购ID
status
string
false
none
1.申购中、 3.申购成功 4.失败,
42.394.1. Enumerated Values
Property
Value
lendingType
CUSTOMIZED_FIXED


---

## Page 229

sapi-v7.4.md
2024-05-08
229 / 419
Property
Value
lendingType
DAILY
lendingType
EXPERIENCE_COUPON
lendingType
REGULAR
lendingType
SUPER_MINING
status
FAILED
status
PURCHASING
status
SUCCESS
PurchaseResp
{ 
  "positionId": 0, 
  "success": true 
} 
 
PurchaseResp
42.395. Properties
Name
Type
Required
Restrictions
Description
positionId
integer(int64)
false
none
none
success
boolean
false
none
none
QueryAccountFundAutoApiKeyResp
{ 
  "apiKeys": [ 
    { 
      "apiName": "string", 
      "apikey": "string", 
      "keyId": 0, 
      "ruleId": 0, 
      "tradeIp": "string", 
      "withdrawIp": "string" 
    } 
  ] 
} 
 
QueryAccountFundAutoApiKeyResp
42.396. Properties
Name
Type
Required
Restrictions
Description
apiKeys
[QuerySubAccountFundAutoApiKeyVo]
false
none
apiKeys
QueryAllOcoOrderListResp
{ 
  "contingencyType": "string", 
  "isIsolated": true, 
  "listClientOrderId": "string", 
  "listOrderStatus": "string", 
  "listStatusType": "string", 
  "orderListId": 0, 
  "orders": [ 
    { 
      "orderId": 0 
    } 
  ], 
  "symbol": "string", 
  "transactionTime": 0 


---

## Page 230

sapi-v7.4.md
2024-05-08
230 / 419
} 
 
QueryAllOcoOrderListResp
42.397. Properties
Name
Type
Required
Restrictions
Description
contingencyType
string
false
none
none
isIsolated
boolean
false
none
none
listClientOrderId
string
false
none
none
listOrderStatus
string
false
none
none
listStatusType
string
false
none
none
orderListId
integer(int64)
false
none
none
orders
[Order]
false
none
none
symbol
string
false
none
none
transactionTime
integer(int64)
false
none
none
QueryAssetByTypeVo
{ 
  "data": {}, 
  "type": "string", 
  "updateTime": 0 
} 
 
QueryAssetByTypeVo
42.398. Properties
Name
Type
Required
Restrictions
Description
data
object
false
none
none
type
string
false
none
none
updateTime
integer(int64)
false
none
none
QueryAssetDetailResp
{ 
  "depositStatus": true, 
  "depositTip": "string", 
  "minWithdrawAmount": 0, 
  "withdrawFee": 0, 
  "withdrawStatus": true 
} 
 
QueryAssetDetailResp
42.399. Properties
Name
Type
Required
Restrictions
Description
depositStatus
boolean
false
none
none
depositTip
string
false
none
none
minWithdrawAmount
number
false
none
none
withdrawFee
number
false
none
none
withdrawStatus
boolean
false
none
none
QueryBrokerSubAccountDeliveryAccountResp


---

## Page 231

sapi-v7.4.md
2024-05-08
231 / 419
{ 
  "assets": [ 
    { 
      "asset": "string", 
      "initialMargin": "string", 
      "maintenanceMargin": "string", 
      "marginBalance": "string", 
      "maxWithdrawAmount": "string", 
      "openOrderInitialMargin": "string", 
      "positionInitialMargin": "string", 
      "unrealizedProfit": "string", 
      "updateTime": 0, 
      "walletBalance": "string" 
    } 
  ], 
  "canDeposit": true, 
  "canTrade": true, 
  "canWithdraw": true, 
  "email": "string", 
  "feeTier": 0, 
  "updateTime": 0 
} 
 
QueryBrokerSubAccountDeliveryAccountResp
42.400. Properties
Name
Type
Required
Restrictions
Description
assets
[DeliveryAssetRiskInfoVo]
false
none
none
canDeposit
boolean
false
none
none
canTrade
boolean
false
none
none
canWithdraw
boolean
false
none
none
email
string
false
none
none
feeTier
integer(int32)
false
none
none
updateTime
integer(int64)
false
none
none
QueryBrokerSubAccountFutureAccountResp
{ 
  "asset": "string", 
  "assets": [ 
    { 
      "asset": "string", 
      "initialMargin": "string", 
      "maintenanceMargin": "string", 
      "marginBalance": "string", 
      "maxWithdrawAmount": "string", 
      "openOrderInitialMargin": "string", 
      "positionInitialMargin": "string", 
      "unrealizedProfit": "string", 
      "updateTime": 0, 
      "walletBalance": "string" 
    } 
  ], 
  "canDeposit": true, 
  "canTrade": true, 
  "canWithdraw": true, 
  "email": "string", 
  "feeTier": 0, 
  "maxWithdrawAmount": "string", 
  "totalInitialMargin": "string", 
  "totalMaintenanceMargin": "string", 
  "totalMarginBalance": "string", 
  "totalOpenOrderInitialMargin": "string", 
  "totalPositionInitialMargin": "string", 
  "totalUnrealizedProfit": "string", 
  "totalWalletBalance": "string", 
  "updateTime": 0 
} 
 


---

## Page 232

sapi-v7.4.md
2024-05-08
232 / 419
QueryBrokerSubAccountFutureAccountResp
42.401. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
assets
[FutureAssetRiskInfoVo]
false
none
none
canDeposit
boolean
false
none
none
canTrade
boolean
false
none
none
canWithdraw
boolean
false
none
none
email
string
false
none
none
feeTier
integer(int32)
false
none
none
maxWithdrawAmount
string
false
none
none
totalInitialMargin
string
false
none
none
totalMaintenanceMargin
string
false
none
none
totalMarginBalance
string
false
none
none
totalOpenOrderInitialMargin
string
false
none
none
totalPositionInitialMargin
string
false
none
none
totalUnrealizedProfit
string
false
none
none
totalWalletBalance
string
false
none
none
updateTime
integer(int64)
false
none
none
QueryBrokerSubAccountResp
{ 
  "createTime": 0, 
  "email": "string", 
  "makerCommission": "string", 
  "marginMakerCommission": "string", 
  "marginTakerCommission": "string", 
  "subaccountId": "string", 
  "tag": "string", 
  "takerCommission": "string" 
} 
 
QueryBrokerSubAccountResp
42.402. Properties
Name
Type
Required
Restrictions
Description
createTime
integer(int64)
false
none
none
email
string
false
none
none
makerCommission
string
false
none
none
marginMakerCommission
string
false
none
none
marginTakerCommission
string
false
none
none
subaccountId
string
false
none
none
tag
string
false
none
none
takerCommission
string
false
none
none
QueryBrokerSubUserApiRes
{ 
  "apiKey": "string", 
  "canTrade": true, 
  "futuresTrade": true, 
  "marginTrade": true, 
  "subaccountId": "string" 


---

## Page 233

sapi-v7.4.md
2024-05-08
233 / 419
} 
 
QueryBrokerSubUserApiRes
42.403. Properties
Name
Type
Required
Restrictions
Description
apiKey
string
false
none
none
canTrade
boolean
false
none
none
futuresTrade
boolean
false
none
none
marginTrade
boolean
false
none
none
subaccountId
string
false
none
none
QueryConvertibleCoinResp
{ 
  "coins": [ 
    "string" 
  ], 
  "convertEnabled": true, 
  "exchangeRates": { 
    "property1": "string", 
    "property2": "string" 
  } 
} 
 
QueryConvertibleCoinResp
42.404. Properties
Name
Type
Required
Restrictions
Description
coins
[string]
false
none
none
convertEnabled
boolean
false
none
none
exchangeRates
object
false
none
none
» additionalProperties
string
false
none
none
QueryDeliveryAccountSummaryResp
{ 
  "asset": "string", 
  "subAccountList": [ 
    { 
      "asset": "string", 
      "email": "string", 
      "totalMarginBalance": "string", 
      "totalUnrealizedProfit": "string", 
      "totalWalletBalance": "string" 
    } 
  ], 
  "totalMarginBalanceOfBTC": "string", 
  "totalUnrealizedProfitOfBTC": "string", 
  "totalWalletBalanceOfBTC": "string" 
} 
 
QueryDeliveryAccountSummaryResp
42.405. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
subAccountList
[DeliveryAccountSummaryInfoVoSapiVersion]
false
none
none


---

## Page 234

sapi-v7.4.md
2024-05-08
234 / 419
Name
Type
Required
Restrictions
Description
totalMarginBalanceOfBTC
string
false
none
none
totalUnrealizedProfitOfBTC
string
false
none
none
totalWalletBalanceOfBTC
string
false
none
none
QueryFiatDepositResponse
{ 
  "fiatDepositLogVoList": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "brokerSubAccountId": "string", 
      "clientDepositId": "string", 
      "createTime": 0, 
      "depositId": 0, 
      "status": "string", 
      "updateTime": 0 
    } 
  ], 
  "total": 0 
} 
 
QueryFiatDepositResponse
42.406. Properties
Name
Type
Required
Restrictions
Description
fiatDepositLogVoList
[FiatDepositLogVo]
false
none
none
total
integer(int64)
false
none
none
QueryFiatWithdrawResponse
{ 
  "fiatWithdrawLogVoList": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "brokerSubAccountId": "string", 
      "clientWithdrawId": "string", 
      "commission": 0, 
      "commissionSubAccountId": "string", 
      "createTime": 0, 
      "status": "string", 
      "updateTime": 0, 
      "withdrawId": 0 
    } 
  ], 
  "total": 0 
} 
 
QueryFiatWithdrawResponse
42.407. Properties
Name
Type
Required
Restrictions
Description
fiatWithdrawLogVoList
[FiatWithdrawLogVo]
false
none
none
total
integer(int64)
false
none
none
QueryFuturesAccountSummaryResp
{ 
  "asset": "string", 
  "subAccountList": [ 
    { 
      "asset": "string", 


---

## Page 235

sapi-v7.4.md
2024-05-08
235 / 419
      "email": "string", 
      "totalInitialMargin": "string", 
      "totalMaintenanceMargin": "string", 
      "totalMarginBalance": "string", 
      "totalOpenOrderInitialMargin": "string", 
      "totalPositionInitialMargin": "string", 
      "totalUnrealizedProfit": "string", 
      "totalWalletBalance": "string" 
    } 
  ], 
  "totalInitialMargin": "string", 
  "totalMaintenanceMargin": "string", 
  "totalMarginBalance": "string", 
  "totalOpenOrderInitialMargin": "string", 
  "totalPositionInitialMargin": "string", 
  "totalUnrealizedProfit": "string", 
  "totalWalletBalance": "string" 
} 
 
QueryFuturesAccountSummaryResp
42.408. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
subAccountList
[FutureAccountSummaryInfoVoSapiVersion]
false
none
none
totalInitialMargin
string
false
none
none
totalMaintenanceMargin
string
false
none
none
totalMarginBalance
string
false
none
none
totalOpenOrderInitialMargin
string
false
none
none
totalPositionInitialMargin
string
false
none
none
totalUnrealizedProfit
string
false
none
none
totalWalletBalance
string
false
none
none
QueryHisTradeResp
{ 
  "commission": 0, 
  "commissionAsset": "string", 
  "id": 0, 
  "isBestMatch": true, 
  "isBuyer": true, 
  "isIsolated": true, 
  "isMaker": true, 
  "orderId": 0, 
  "price": 0, 
  "qty": 0, 
  "quoteQty": 0, 
  "symbol": "string", 
  "time": 0 
} 
 
QueryHisTradeResp
42.409. Properties
Name
Type
Required
Restrictions
Description
commission
number
false
none
none
commissionAsset
string
false
none
none
id
integer(int64)
false
none
none
isBestMatch
boolean
false
none
none
isBuyer
boolean
false
none
none
isIsolated
boolean
false
none
none


---

## Page 236

sapi-v7.4.md
2024-05-08
236 / 419
Name
Type
Required
Restrictions
Description
isMaker
boolean
false
none
none
orderId
integer(int64)
false
none
none
price
number
false
none
none
qty
number
false
none
none
quoteQty
number
false
none
none
symbol
string
false
none
none
time
integer(int64)
false
none
none
QueryIsolatedMarginAccountSummaryResp
{ 
  "isolatedMarginSummaries": [ 
    { 
      "email": "string", 
      "status": 0, 
      "subUserId": 0, 
      "totalAssetOfBtc": 0, 
      "totalLiabilityOfBtc": 0, 
      "totalNetAssetOfBtc": 0 
    } 
  ], 
  "totalAssetOfBtc": "string", 
  "totalLiabilityOfBtc": "string", 
  "totalNetAssetOfBtc": "string", 
  "totalSubAccountSize": 0 
} 
 
QueryIsolatedMarginAccountSummaryResp
42.410. Properties
Name
Type
Required
Restrictions
Description
isolatedMarginSummaries
[UserTotalAssetSummary]
false
none
none
totalAssetOfBtc
string
false
none
所有⼦账户总资产（单位：BTC
totalLiabilityOfBtc
string
false
none
所有⼦账户总负债（单位：BTC
totalNetAssetOfBtc
string
false
none
所有⼦账户净资产（单位：BTC
totalSubAccountSize
integer(int64)
false
none
none
QueryManagerSubUserInfoResp
{ 
  "managerSubUserInfoVoList": [ 
    { 
      "bindParentEmail": "string", 
      "bindParentUserId": 0, 
      "email": "string", 
      "insertTimeStamp": 0, 
      "isFutureEnabled": true, 
      "isMarginEnabled": true, 
      "isSignedLVTRiskAgreement": true, 
      "isSubUserEnabled": true, 
      "isUserActive": true, 
      "managersubUserId": 0, 
      "remark": "string", 
      "rootUserId": 0 
    } 
  ], 
  "total": 0 
} 
 
QueryManagerSubUserInfoResp
42.411. Properties


---

## Page 237

sapi-v7.4.md
2024-05-08
237 / 419
Name
Type
Required
Restrictions
Description
managerSubUserInfoVoList
[ManagerSubUserInfoVo]
true
none
分⻚数据
total
integer(int64)
true
none
total
QueryMarginAccountSummaryResp
{ 
  "subAccountList": [ 
    { 
      "email": "string", 
      "totalAssetOfBtc": "string", 
      "totalLiabilityOfBtc": "string", 
      "totalNetAssetOfBtc": "string" 
    } 
  ], 
  "totalAssetOfBtc": "string", 
  "totalLiabilityOfBtc": "string", 
  "totalNetAssetOfBtc": "string" 
} 
 
QueryMarginAccountSummaryResp
42.412. Properties
Name
Type
Required
Restrictions
Description
subAccountList
[MarginAccountSummaryInfoVoSapiVersion]
false
none
none
totalAssetOfBtc
string
false
none
所有⼦账户总资产（单位：BTC
totalLiabilityOfBtc
string
false
none
所有⼦账户总负债（单位：BTC
totalNetAssetOfBtc
string
false
none
所有⼦账户净资产（单位：BTC
QueryMarginUserMicroassetsResp
{ 
  "total": 0, 
  "userAssetDribblets": [ 
    { 
      "operateTime": "2019-08-24T14:15:22Z", 
      "totalServiceChargeAmount": 0, 
      "totalTransferedAmount": 0, 
      "transId": 0, 
      "userAssetDribbletDetails": [ 
        { 
          "amount": 0, 
          "fromAsset": "string", 
          "operateTime": "2019-08-24T14:15:22Z", 
          "serviceChargeAmount": 0, 
          "transId": 0, 
          "transferedAmount": 0, 
          "uid": "string" 
        } 
      ] 
    } 
  ] 
} 
 
QueryMarginUserMicroassetsResp
42.413. Properties
Name
Type
Required
Restrictions
Description
total
integer(int32)
false
none
none
userAssetDribblets
[MarginUserMicroassets]
false
none
none
QueryNLMigrationLogsRes


---

## Page 238

sapi-v7.4.md
2024-05-08
238 / 419
{ 
  "migrateLogs": [ 
    { 
      "assetDetails": [ 
        { 
          "amount": 0, 
          "asset": "string" 
        } 
      ], 
      "migrateTime": 0, 
      "tranId": 0 
    } 
  ] 
} 
 
QueryNLMigrationLogsRes
42.414. Properties
Name
Type
Required
Restrictions
Description
migrateLogs
[MigrateLog]
false
none
migration records, one user can have multiple migrations
QueryNLReverseLogsRes
{ 
  "reverseLogs": [ 
    { 
      "assetDetails": [ 
        { 
          "amount": 0, 
          "asset": "string" 
        } 
      ], 
      "reverseTime": 0, 
      "tranId": 0 
    } 
  ] 
} 
 
QueryNLReverseLogsRes
42.415. Properties
Name
Type
Required
Restrictions
Description
reverseLogs
[ReverseLog]
false
none
reverse records, one user can have multiple reverse records
QueryOcoOpenOrderListResp
{ 
  "contingencyType": "string", 
  "isIsolated": true, 
  "listClientOrderId": "string", 
  "listOrderStatus": "string", 
  "listStatusType": "string", 
  "orderListId": 0, 
  "orders": [ 
    { 
      "orderId": 0 
    } 
  ], 
  "symbol": "string", 
  "transactionTime": 0 
} 
 
QueryOcoOpenOrderListResp
42.416. Properties


---

## Page 239

sapi-v7.4.md
2024-05-08
239 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
contingencyType
string
false
none
none
isIsolated
boolean
false
none
none
listClientOrderId
string
false
none
none
listOrderStatus
string
false
none
none
listStatusType
string
false
none
none
orderListId
integer(int64)
false
none
none
orders
[Order]
false
none
none
symbol
string
false
none
none
transactionTime
integer(int64)
false
none
none
QueryOcoOrderListResp
{ 
  "contingencyType": "string", 
  "isIsolated": true, 
  "listClientOrderId": "string", 
  "listOrderStatus": "string", 
  "listStatusType": "string", 
  "orderListId": 0, 
  "orders": [ 
    { 
      "orderId": 0 
    } 
  ], 
  "symbol": "string", 
  "transactionTime": 0 
} 
 
QueryOcoOrderListResp
42.417. Properties
Name
Type
Required
Restrictions
Description
contingencyType
string
false
none
none
isIsolated
boolean
false
none
none
listClientOrderId
string
false
none
none
listOrderStatus
string
false
none
none
listStatusType
string
false
none
none
orderListId
integer(int64)
false
none
none
orders
[Order]
false
none
none
symbol
string
false
none
none
transactionTime
integer(int64)
false
none
none
QueryOpenEntrustmentResp
{ 
  "clientOrderId": "string", 
  "cummulativeQuoteQty": 0, 
  "executedQty": 0, 
  "icebergQty": 0, 
  "isIsolated": true, 
  "isWorking": true, 
  "orderId": 0, 
  "origQty": 0, 
  "price": 0, 
  "selfTradePreventionMode": "string", 
  "side": "string", 
  "status": "string", 
  "stopPrice": 0, 
  "symbol": "string", 
  "time": 0, 


---

## Page 240

sapi-v7.4.md
2024-05-08
240 / 419
  "timeInForce": "string", 
  "type": "string", 
  "updateTime": 0 
} 
 
QueryOpenEntrustmentResp
42.418. Properties
Name
Type
Required
Restrictions
Description
clientOrderId
string
false
none
none
cummulativeQuoteQty
number
false
none
none
executedQty
number
false
none
none
icebergQty
number
false
none
none
isIsolated
boolean
false
none
none
isWorking
boolean
false
none
none
orderId
integer(int64)
false
none
none
origQty
number
false
none
none
price
number
false
none
none
selfTradePreventionMode
string
false
none
none
side
string
false
none
none
status
string
false
none
none
stopPrice
number
false
none
none
symbol
string
false
none
none
time
integer(int64)
false
none
none
timeInForce
string
false
none
none
type
string
false
none
none
updateTime
integer(int64)
false
none
none
QueryResponse
{} 
 
QueryResponse
42.419. Properties
None
QuerySpotSummaryResp
{ 
  "masterAccountTotalAsset": 0, 
  "spotSubUserAssetBtcVoList": [ 
    { 
      "email": "string", 
      "totalAsset": 0 
    } 
  ], 
  "totalCount": 0 
} 
 
QuerySpotSummaryResp
42.420. Properties
Name
Type
Required
Restrictions
Description


---

## Page 241

sapi-v7.4.md
2024-05-08
241 / 419
Name
Type
Required
Restrictions
Description
masterAccountTotalAsset
number
false
none
none
spotSubUserAssetBtcVoList
[SpotSubUserAssetBtcVo]
false
none
none
totalCount
integer(int64)
false
none
none
QuerySubAccountDeliveryAccountResp
{ 
  "assets": [ 
    { 
      "asset": "string", 
      "initialMargin": "string", 
      "maintenanceMargin": "string", 
      "marginBalance": "string", 
      "maxWithdrawAmount": "string", 
      "openOrderInitialMargin": "string", 
      "positionInitialMargin": "string", 
      "unrealizedProfit": "string", 
      "updateTime": 0, 
      "walletBalance": "string" 
    } 
  ], 
  "canDeposit": true, 
  "canTrade": true, 
  "canWithdraw": true, 
  "email": "string", 
  "feeTier": 0, 
  "updateTime": 0 
} 
 
QuerySubAccountDeliveryAccountResp
42.421. Properties
Name
Type
Required
Restrictions
Description
assets
[DeliveryAssetRiskInfoVo]
false
none
none
canDeposit
boolean
false
none
none
canTrade
boolean
false
none
none
canWithdraw
boolean
false
none
none
email
string
false
none
none
feeTier
integer(int32)
false
none
none
updateTime
integer(int64)
false
none
none
QuerySubAccountFundAutoApiKeyResp
{ 
  "apiKeys": [ 
    { 
      "apiName": "string", 
      "apikey": "string", 
      "keyId": 0, 
      "ruleId": 0, 
      "tradeIp": "string", 
      "withdrawIp": "string" 
    } 
  ] 
} 
 
QuerySubAccountFundAutoApiKeyResp
42.422. Properties
Name
Type
Required
Restrictions
Description
apiKeys
[QuerySubAccountFundAutoApiKeyVo]
false
none
apiKeys


---

## Page 242

sapi-v7.4.md
2024-05-08
242 / 419
QuerySubAccountFundAutoApiKeyVo
{ 
  "apiName": "string", 
  "apikey": "string", 
  "keyId": 0, 
  "ruleId": 0, 
  "tradeIp": "string", 
  "withdrawIp": "string" 
} 
 
QuerySubAccountFundAutoApiKeyVo
42.423. Properties
Name
Type
Required
Restrictions
Description
apiName
string
false
none
API名称
apikey
string
false
none
apikey
keyId
integer(int64)
false
none
keyId
ruleId
integer(int64)
false
none
ruleId
tradeIp
string
false
none
tradeIp
withdrawIp
string
false
none
withdrawIp
QuerySubAccountFutureAccountResp
{ 
  "asset": "string", 
  "assets": [ 
    { 
      "asset": "string", 
      "initialMargin": "string", 
      "maintenanceMargin": "string", 
      "marginBalance": "string", 
      "maxWithdrawAmount": "string", 
      "openOrderInitialMargin": "string", 
      "positionInitialMargin": "string", 
      "unrealizedProfit": "string", 
      "updateTime": 0, 
      "walletBalance": "string" 
    } 
  ], 
  "canDeposit": true, 
  "canTrade": true, 
  "canWithdraw": true, 
  "email": "string", 
  "feeTier": 0, 
  "maxWithdrawAmount": "string", 
  "totalInitialMargin": "string", 
  "totalMaintenanceMargin": "string", 
  "totalMarginBalance": "string", 
  "totalOpenOrderInitialMargin": "string", 
  "totalPositionInitialMargin": "string", 
  "totalUnrealizedProfit": "string", 
  "totalWalletBalance": "string", 
  "updateTime": 0 
} 
 
QuerySubAccountFutureAccountResp
42.424. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
assets
[FutureAssetRiskInfoVo]
false
none
none
canDeposit
boolean
false
none
none


---

## Page 243

sapi-v7.4.md
2024-05-08
243 / 419
Name
Type
Required
Restrictions
Description
canTrade
boolean
false
none
none
canWithdraw
boolean
false
none
none
email
string
false
none
none
feeTier
integer(int32)
false
none
none
maxWithdrawAmount
string
false
none
none
totalInitialMargin
string
false
none
none
totalMaintenanceMargin
string
false
none
none
totalMarginBalance
string
false
none
none
totalOpenOrderInitialMargin
string
false
none
none
totalPositionInitialMargin
string
false
none
none
totalUnrealizedProfit
string
false
none
none
totalWalletBalance
string
false
none
none
updateTime
integer(int64)
false
none
none
QuerySubAccountMarginAccountRespSapiVersion
{ 
  "email": "string", 
  "marginLevel": "string", 
  "marginTradeCoeffVo": { 
    "canTrade": true, 
    "forceLiquidationBar": 0, 
    "marginCallBar": 0, 
    "normalBar": 0 
  }, 
  "marginUserAssetVoList": [ 
    { 
      "asset": "string", 
      "borrowed": "string", 
      "free": "string", 
      "interest": "string", 
      "locked": "string", 
      "netAsset": "string" 
    } 
  ], 
  "totalAssetOfBtc": "string", 
  "totalLiabilityOfBtc": "string", 
  "totalNetAssetOfBtc": "string" 
} 
 
QuerySubAccountMarginAccountRespSapiVersion
42.425. Properties
Name
Type
Required
Restrictions
Description
email
string
false
none
none
marginLevel
string
false
none
⻛险率
marginTradeCoeffVo
MarginTradeCoeffVoSapiVersion
false
none
none
marginUserAssetVoList
[MarginUserAssetVoSapiVersion]
false
none
资产信息
totalAssetOfBtc
string
false
none
总资产（单位：BTC）
totalLiabilityOfBtc
string
false
none
总负债（单位：BTC）
totalNetAssetOfBtc
string
false
none
净资产（单位：BTC）
QuerySubUserStatusResp
{ 
  "msg": "string", 
  "subAccounts": [ 
    { 


---

## Page 244

sapi-v7.4.md
2024-05-08
244 / 419
      "createTime": "2019-08-24T14:15:22Z", 
      "email": "string", 
      "isAssetManagementSubAccount": true, 
      "isFreeze": true, 
      "isManagedSubAccount": true 
    } 
  ], 
  "success": true 
} 
 
QuerySubUserStatusResp
42.426. Properties
Name
Type
Required
Restrictions
Description
msg
string
false
none
none
subAccounts
[SubAccountBriefVo]
false
none
none
success
boolean
false
none
none
QueryTransferPageResponse
{ 
  "amount": 0, 
  "asset": "string", 
  "createTime": "2019-08-24T14:15:22Z", 
  "openId": "string", 
  "orderId": "string", 
  "status": "string", 
  "tranType": "IN" 
} 
 
QueryTransferPageResponse
42.427. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
createTime
string(date-time)
false
none
none
openId
string
false
none
none
orderId
string
false
none
none
status
string
false
none
none
tranType
string
false
none
none
42.427.1. Enumerated Values
Property
Value
tranType
IN
tranType
OUT
QueryUserMicroassetsResp
{ 
  "total": 0, 
  "userAssetDribblets": [ 
    { 
      "clientId": "string", 
      "operateTime": "2019-08-24T14:15:22Z", 
      "totalServiceChargeAmount": 0, 
      "totalTransferedAmount": 0, 
      "transId": 0, 
      "userAssetDribbletDetails": [ 
        { 


---

## Page 245

sapi-v7.4.md
2024-05-08
245 / 419
          "amount": 0, 
          "fromAsset": "string", 
          "operateTime": "2019-08-24T14:15:22Z", 
          "serviceChargeAmount": 0, 
          "transId": 0, 
          "transferedAmount": 0, 
          "uid": "string" 
        } 
      ] 
    } 
  ] 
} 
 
QueryUserMicroassetsResp
42.428. Properties
Name
Type
Required
Restrictions
Description
total
integer(int32)
false
none
none
userAssetDribblets
[UserMicroassets]
false
none
none
Quota
{ 
  "minimum": 0, 
  "totalPersonalQuota": 0 
} 
 
Quota
42.429. Properties
Name
Type
Required
Restrictions
Description
minimum
number
false
none
none
totalPersonalQuota
number
false
none
none
QuotaResp
{ 
  "leftPersonalQuota": 0 
} 
 
QuotaResp
42.430. Properties
Name
Type
Required
Restrictions
Description
leftPersonalQuota
number
false
none
none
QuotaResponse
{ 
  "leftRedemptionPersonalQuota": 0, 
  "leftStakingPersonalQuota": 0 
} 
 
QuotaResponse
42.431. Properties
Name
Type
Required
Restrictions
Description
leftRedemptionPersonalQuota
number
false
none
none


---

## Page 246

sapi-v7.4.md
2024-05-08
246 / 419
Name
Type
Required
Restrictions
Description
leftStakingPersonalQuota
number
false
none
none
QuoteResponse
{ 
  "baseCurrency": "string", 
  "baseCurrencySize": "string", 
  "baseCurrencyTokenAddress": "string", 
  "compensationAmount": "string", 
  "compensationCurrency": "string", 
  "compensationCurrencyTokenAddress": "string", 
  "message": "string", 
  "platformSign": "string", 
  "price": 0, 
  "quoteCurrency": "string", 
  "quoteCurrencySize": "string", 
  "quoteCurrencyTokenAddress": "string", 
  "quoteId": "string", 
  "quoteValidTime": 0, 
  "settlementMode": 0, 
  "side": "BUY", 
  "sign": "string" 
} 
 
QuoteResponse
42.432. Properties
Name
Type
Required
Restrictions
Description
baseCurrency
string
false
none
none
baseCurrencySize
string
false
none
none
baseCurrencyTokenAddress
string
false
none
none
compensationAmount
string
false
none
none
compensationCurrency
string
false
none
none
compensationCurrencyTokenAddress
string
false
none
none
message
string
false
none
none
platformSign
string
false
none
none
price
number
false
none
none
quoteCurrency
string
false
none
none
quoteCurrencySize
string
false
none
none
quoteCurrencyTokenAddress
string
false
none
none
quoteId
string
false
none
none
quoteValidTime
integer(int64)
false
none
none
settlementMode
integer(int32)
false
none
none
side
string
false
none
none
sign
string
false
none
none
42.432.1. Enumerated Values
Property
Value
side
BUY
side
SELL
RateHistory
{ 
  "annualPercentageRate": 0, 
  "exchangeRate": "string", 


---

## Page 247

sapi-v7.4.md
2024-05-08
247 / 419
  "time": 0 
} 
 
RateHistory
42.433. Properties
Name
Type
Required
Restrictions
Description
annualPercentageRate
number
false
none
none
exchangeRate
string
false
none
none
time
integer(int64)
false
none
none
RateHistoryResp
{ 
  "annualPercentageRate": 0, 
  "asset": "string", 
  "productId": "string", 
  "time": 0 
} 
 
RateHistoryResp
42.434. Properties
Name
Type
Required
Restrictions
Description
annualPercentageRate
number
false
none
none
asset
string
false
none
none
productId
string
false
none
none
time
integer(int64)
false
none
none
RateHistoryResponse
{ 
  "rows": [ 
    { 
      "annualPercentageRate": 0, 
      "exchangeRate": "string", 
      "time": 0 
    } 
  ], 
  "total": 0 
} 
 
RateHistoryResponse
42.435. Properties
Name
Type
Required
Restrictions
Description
rows
[RateHistory]
false
none
none
total
integer(int64)
false
none
none
ReStakeInfo
{ 
  "estRewards": 0, 
  "reStakeAmount": 0, 
  "reStakeApr": 0, 
  "reStakeDeliverDate": 0, 
  "reStakeDuration": 0, 
  "reStakeRate": 0, 
  "reStakeRewardsEndDate": 0 


---

## Page 248

sapi-v7.4.md
2024-05-08
248 / 419
} 
 
ReStakeInfo
42.436. Properties
Name
Type
Required
Restrictions
Description
estRewards
number
false
none
none
reStakeAmount
number
false
none
none
reStakeApr
number
false
none
none
reStakeDeliverDate
integer(int64)
false
none
none
reStakeDuration
integer(int32)
false
none
none
reStakeRate
number
false
none
none
reStakeRewardsEndDate
integer(int64)
false
none
none
RedeemResp
{ 
  "success": true 
} 
 
RedeemResp
42.437. Properties
Name
Type
Required
Restrictions
Description
success
boolean
false
none
none
RedeemResponse
{ 
  "arrivalTime": 0, 
  "conversionRatio": "string", 
  "ethAmount": 0, 
  "success": true 
} 
 
RedeemResponse
42.438. Properties
Name
Type
Required
Restrictions
Description
arrivalTime
integer(int64)
false
none
none
conversionRatio
string
false
none
none
ethAmount
number
false
none
none
success
boolean
false
none
none
RedemptionHistory
{ 
  "amount": 0, 
  "arrivalTime": 0, 
  "asset": "string", 
  "conversionRatio": "string", 
  "distributeAmount": 0, 
  "distributeAsset": "string", 
  "status": "string", 
  "time": 0 
} 
 


---

## Page 249

sapi-v7.4.md
2024-05-08
249 / 419
RedemptionHistory
42.439. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
arrivalTime
integer(int64)
false
none
none
asset
string
false
none
none
conversionRatio
string
false
none
none
distributeAmount
number
false
none
none
distributeAsset
string
false
none
none
status
string
false
none
none
time
integer(int64)
false
none
none
RedemptionHistoryResponse
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "arrivalTime": 0, 
      "asset": "string", 
      "conversionRatio": "string", 
      "distributeAmount": 0, 
      "distributeAsset": "string", 
      "status": "string", 
      "time": 0 
    } 
  ], 
  "total": 0 
} 
 
RedemptionHistoryResponse
42.440. Properties
Name
Type
Required
Restrictions
Description
rows
[RedemptionHistory]
false
none
none
total
integer(int64)
false
none
none
RedemptionQuotaResp
{ 
  "dailyQuota": 0, 
  "minRedemptionAmount": 0, 
  "personalLeftQuota": 0, 
  "productLeftQuota": 0 
} 
 
RedemptionQuotaResp
42.441. Properties
Name
Type
Required
Restrictions
Description
dailyQuota
number
false
none
none
minRedemptionAmount
number
false
none
none
personalLeftQuota
number
false
none
none
productLeftQuota
number
false
none
none
RedemptionRecord


---

## Page 250

sapi-v7.4.md
2024-05-08
250 / 419
{ 
  "amount": 0, 
  "asset": "string", 
  "deliverDate": 0, 
  "lockPeriod": 0, 
  "positionId": 0, 
  "redeemId": 0, 
  "status": "string", 
  "time": 0, 
  "type": "string" 
} 
 
RedemptionRecord
42.442. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
deliverDate
integer(int64)
false
none
none
lockPeriod
integer(int32)
false
none
none
positionId
integer(int64)
false
none
none
redeemId
integer(int64)
false
none
none
status
string
false
none
none
time
integer(int64)
false
none
none
type
string
false
none
none
RedemptionRecordResp
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "deliverDate": 0, 
      "lockPeriod": 0, 
      "positionId": 0, 
      "redeemId": 0, 
      "status": "string", 
      "time": 0, 
      "type": "string" 
    } 
  ], 
  "total": 0 
} 
 
RedemptionRecordResp
42.443. Properties
Name
Type
Required
Restrictions
Description
rows
[RedemptionRecord]
false
none
none
total
integer(int64)
false
none
none
RedemptionResp
{ 
  "redeemId": 0, 
  "success": true 
} 
 


---

## Page 251

sapi-v7.4.md
2024-05-08
251 / 419
RedemptionResp
42.444. Properties
Name
Type
Required
Restrictions
Description
redeemId
integer(int64)
false
none
none
success
boolean
false
none
none
RepayFuturesSwitchResp
{ 
  "autoRepay": true 
} 
 
RepayFuturesSwitchResp
42.445. Properties
Name
Type
Required
Restrictions
Description
autoRepay
boolean
false
none
none
RetrieveChatMessagesWithPaginationResp
{ 
  "content": "string", 
  "createTime": "2019-08-24T14:15:22Z", 
  "fromNickName": "string", 
  "height": 0, 
  "id": 0, 
  "imageType": "string", 
  "imageUrl": "string", 
  "orderNo": "string", 
  "self": true, 
  "status": "read", 
  "thumbnailUrl": "string", 
  "type": "auto_reply", 
  "uuid": "string", 
  "width": 0 
} 
 
RetrieveChatMessagesWithPaginationResp
42.446. Properties
Name
Type
Required
Restrictions
Description
content
string
false
none
Message content
createTime
string(date-time)
false
none
Insertion time
fromNickName
string
false
none
Sender's nickname
height
integer(int32)
false
none
Image height
id
integer(int64)
false
none
ID
imageType
string
false
none
Image type
imageUrl
string
false
none
Original image URL
orderNo
string
false
none
Order number
self
boolean
false
none
If the message is sent by yourself
status
string
false
none
Message status
thumbnailUrl
string
false
none
Image thumbnail URL
type
string
false
none
Message type (text,image,auto_reply)
uuid
string
false
none
Client message UUID
width
integer(int32)
false
none
Image width


---

## Page 252

sapi-v7.4.md
2024-05-08
252 / 419
42.446.1. Enumerated Values
Property
Value
status
read
status
unread
type
auto_reply
type
card
type
error
type
image
type
mark
type
recall
type
system
type
text
type
translate
type
video
ReverseLog
{ 
  "assetDetails": [ 
    { 
      "amount": 0, 
      "asset": "string" 
    } 
  ], 
  "reverseTime": 0, 
  "tranId": 0 
} 
 
ReverseLog
42.447. Properties
Name
Type
Required
Restrictions
Description
assetDetails
[NLAssetDetail]
false
none
asset details
reverseTime
integer(int64)
false
none
reverse time
tranId
integer(int64)
false
none
reverse tran id
ReverseNLResp
{ 
  "transferResponses": [ 
    { 
      "response": "string", 
      "status": "string", 
      "tranId": 0 
    } 
  ] 
} 
 
ReverseNLResp
42.448. Properties
Name
Type
Required
Restrictions
Description
transferResponses
[transfer_response]
false
none
a list of transfer responses
RewardsHistory


---

## Page 253

sapi-v7.4.md
2024-05-08
253 / 419
{ 
  "amount": 0, 
  "annualPercentageRate": 0, 
  "asset": "string", 
  "holding": 0, 
  "status": "string", 
  "time": 0 
} 
 
RewardsHistory
42.449. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
annualPercentageRate
number
false
none
none
asset
string
false
none
none
holding
number
false
none
none
status
string
false
none
none
time
integer(int64)
false
none
none
RewardsHistoryResponse
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "annualPercentageRate": 0, 
      "asset": "string", 
      "holding": 0, 
      "status": "string", 
      "time": 0 
    } 
  ], 
  "total": 0 
} 
 
RewardsHistoryResponse
42.450. Properties
Name
Type
Required
Restrictions
Description
rows
[RewardsHistory]
false
none
none
total
integer(int64)
false
none
none
RewardsRecord
{ 
  "amount": 0, 
  "asset": "string", 
  "lockPeriod": 0, 
  "positionId": 0, 
  "time": 0 
} 
 
RewardsRecord
42.451. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none


---

## Page 254

sapi-v7.4.md
2024-05-08
254 / 419
Name
Type
Required
Restrictions
Description
lockPeriod
integer(int32)
false
none
none
positionId
integer(int64)
false
none
none
time
integer(int64)
false
none
none
RewardsRecordResp
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "lockPeriod": 0, 
      "positionId": 0, 
      "time": 0 
    } 
  ], 
  "total": 0 
} 
 
RewardsRecordResp
42.452. Properties
Name
Type
Required
Restrictions
Description
rows
[RewardsRecord]
false
none
none
total
integer(int64)
false
none
none
RfqDcSettlementDetailSapiResp
{ 
  "code": "string", 
  "detailList": [ 
    { 
      "bnPayingAmount": 0, 
      "bnPayingToken": "string", 
      "bnReceivingAmount": 0, 
      "bnReceivingToken": "string", 
      "createTime": 0, 
      "depositAmount": 0, 
      "depositAsset": "string", 
      "fixingTime": 0, 
      "isExercised": true, 
      "positionId": 0, 
      "premiumAmount": 0, 
      "underlyingPair": [ 
        "string" 
      ] 
    } 
  ], 
  "fixingTime": 0, 
  "message": "string", 
  "totalCount": 0 
} 
 
RfqDcSettlementDetailSapiResp
42.453. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
detailList
[RfqDcSubscriptionSettlementDetailSapiResp]
false
none
none
fixingTime
integer(int64)
false
none
none
message
string
false
none
none
totalCount
integer(int32)
false
none
none


---

## Page 255

sapi-v7.4.md
2024-05-08
255 / 419
RfqDcSettlementReconConfirmArg
{ 
  "fixingTime": 0, 
  "isExercised": true 
} 
 
RfqDcSettlementReconConfirmArg
42.454. Properties
Name
Type
Required
Restrictions
Description
fixingTime
integer(int64)
false
none
none
isExercised
boolean
false
none
none
RfqDcSettlementReconSapiResp
{ 
  "code": "string", 
  "fixingTime": 0, 
  "message": "string" 
} 
 
RfqDcSettlementReconSapiResp
42.455. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
fixingTime
integer(int64)
false
none
none
message
string
false
none
none
RfqDcSettlementSummaryDetailSapiResp
{ 
  "bnPayingAmount": 0, 
  "bnReceivingAmount": 0, 
  "coin": "string", 
  "fixingTime": 0, 
  "totalNettingAmount": 0 
} 
 
RfqDcSettlementSummaryDetailSapiResp
42.456. Properties
Name
Type
Required
Restrictions
Description
bnPayingAmount
number
false
none
none
bnReceivingAmount
number
false
none
none
coin
string
false
none
none
fixingTime
integer(int64)
false
none
none
totalNettingAmount
number
false
none
none
RfqDcSettlementSummarySapiResp
{ 
  "code": "string", 
  "fixingTime": 0, 
  "message": "string", 
  "summaryList": [ 


---

## Page 256

sapi-v7.4.md
2024-05-08
256 / 419
    { 
      "bnPayingAmount": 0, 
      "bnReceivingAmount": 0, 
      "coin": "string", 
      "fixingTime": 0, 
      "totalNettingAmount": 0 
    } 
  ] 
} 
 
RfqDcSettlementSummarySapiResp
42.457. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
fixingTime
integer(int64)
false
none
none
message
string
false
none
none
summaryList
[RfqDcSettlementSummaryDetailSapiResp]
false
none
none
RfqDcSubscriptionSettlementDetailSapiResp
{ 
  "bnPayingAmount": 0, 
  "bnPayingToken": "string", 
  "bnReceivingAmount": 0, 
  "bnReceivingToken": "string", 
  "createTime": 0, 
  "depositAmount": 0, 
  "depositAsset": "string", 
  "fixingTime": 0, 
  "isExercised": true, 
  "positionId": 0, 
  "premiumAmount": 0, 
  "underlyingPair": [ 
    "string" 
  ] 
} 
 
RfqDcSubscriptionSettlementDetailSapiResp
42.458. Properties
Name
Type
Required
Restrictions
Description
bnPayingAmount
number
false
none
none
bnPayingToken
string
false
none
none
bnReceivingAmount
number
false
none
none
bnReceivingToken
string
false
none
none
createTime
integer(int64)
false
none
none
depositAmount
number
false
none
none
depositAsset
string
false
none
none
fixingTime
integer(int64)
false
none
none
isExercised
boolean
false
none
none
positionId
integer(int64)
false
none
none
premiumAmount
number
false
none
none
underlyingPair
[string]
false
none
none
RiskWarningTips
{ 
  "riskTips": "string", 


---

## Page 257

sapi-v7.4.md
2024-05-08
257 / 419
  "riskType": "string" 
} 
 
RiskWarningTips
42.459. Properties
Name
Type
Required
Restrictions
Description
riskTips
string
false
none
Risk warning tips
riskType
string
false
none
Risk type: (fiat, paymethod, counterparty)
RiskWarningTipsReq
{ 
  "fiat": "string", 
  "orderNo": "string", 
  "scene": "string" 
} 
 
RiskWarningTipsReq
42.460. Properties
Name
Type
Required
Restrictions
Description
fiat
string
false
none
iat currency: CNY
orderNo
string
false
none
Order number
scene
string
false
none
Risk scene (Portal, Chat)
RiskWarningTipsResp
{ 
  "riskHints": [ 
    { 
      "riskTips": "string", 
      "riskType": "string" 
    } 
  ] 
} 
 
RiskWarningTipsResp
42.461. Properties
Name
Type
Required
Restrictions
Description
riskHints
[RiskWarningTips]
false
none
Risk hint list
SapiCreateListenKeyResponse
{ 
  "listenKey": "string" 
} 
 
SapiCreateListenKeyResponse
42.462. Properties
Name
Type
Required
Restrictions
Description
listenKey
string
false
none
none
SapiGetQuoteResponse


---

## Page 258

sapi-v7.4.md
2024-05-08
258 / 419
{ 
  "commissionAmount": 0, 
  "commissionCoin": "string", 
  "fromAmount": 0, 
  "inverseRatio": 0, 
  "quoteId": "string", 
  "ratio": 0, 
  "symbol": "string", 
  "toAmount": 0, 
  "validTimestamp": 0 
} 
 
SapiGetQuoteResponse
42.463. Properties
Name
Type
Required
Restrictions
Description
commissionAmount
number
false
none
none
commissionCoin
string
false
none
none
fromAmount
number
false
none
none
inverseRatio
number
false
none
none
quoteId
string
false
none
none
ratio
number
false
none
none
symbol
string
false
none
none
toAmount
number
false
none
none
validTimestamp
integer(int64)
false
none
none
SapiTradeFlowResponse
{ 
  "endTime": 0, 
  "limit": 0, 
  "list": [ 
    { 
      "createTime": 0, 
      "fromAmount": 0, 
      "fromAsset": "string", 
      "inverseRatio": 0, 
      "orderId": 0, 
      "orderStatus": "string", 
      "orderType": "string", 
      "quoteId": "string", 
      "ratio": 0, 
      "side": "string", 
      "toAmount": 0, 
      "toAsset": "string" 
    } 
  ], 
  "moreData": true, 
  "startTime": 0 
} 
 
SapiTradeFlowResponse
42.464. Properties
Name
Type
Required
Restrictions
Description
endTime
integer(int64)
false
none
none
limit
integer(int32)
false
none
none
list
[SapiTradeOrderResponse]
false
none
none
moreData
boolean
false
none
none
startTime
integer(int64)
false
none
none


---

## Page 259

sapi-v7.4.md
2024-05-08
259 / 419
SapiTradeOrderResponse
{ 
  "createTime": 0, 
  "fromAmount": 0, 
  "fromAsset": "string", 
  "inverseRatio": 0, 
  "orderId": 0, 
  "orderStatus": "string", 
  "orderType": "string", 
  "quoteId": "string", 
  "ratio": 0, 
  "side": "string", 
  "toAmount": 0, 
  "toAsset": "string" 
} 
 
SapiTradeOrderResponse
42.465. Properties
Name
Type
Required
Restrictions
Description
createTime
integer(int64)
false
none
none
fromAmount
number
false
none
none
fromAsset
string
false
none
none
inverseRatio
number
false
none
none
orderId
integer(int64)
false
none
none
orderStatus
string
false
none
none
orderType
string
false
none
none
quoteId
string
false
none
none
ratio
number
false
none
none
side
string
false
none
none
toAmount
number
false
none
none
toAsset
string
false
none
none
SapiUserSettlementResp
{ 
  "quoteId": "string", 
  "status": "string" 
} 
 
SapiUserSettlementResp
42.466. Properties
Name
Type
Required
Restrictions
Description
quoteId
string
false
none
none
status
string
false
none
none
SaveSettlementPriceReq
{ 
  "list": [ 
    { 
      "fixingPrice": 0, 
      "fixingTime": 0, 
      "fromAsset": "string", 
      "toAsset": "string" 
    } 
  ] 


---

## Page 260

sapi-v7.4.md
2024-05-08
260 / 419
} 
 
SaveSettlementPriceReq
42.467. Properties
Name
Type
Required
Restrictions
Description
list
[Price]
false
none
none
SaveSettlementPriceResp
{ 
  "code": 0, 
  "msg": "string" 
} 
 
SaveSettlementPriceResp
42.468. Properties
Name
Type
Required
Restrictions
Description
code
integer(int32)
false
none
none
msg
string
false
none
none
SelectApiAgentCodeAliasRes
{ 
  "customerId": "string", 
  "email": "string", 
  "refereeId": 0 
} 
 
SelectApiAgentCodeAliasRes
42.469. Properties
Name
Type
Required
Restrictions
Description
customerId
string
false
none
三⽅备注id
email
string
false
none
email
refereeId
integer(int64)
false
none
被推荐⼈id
SelectBrokerFutureTransferRes
{ 
  "asset": "string", 
  "clientTranId": "string", 
  "from": "string", 
  "qty": "string", 
  "time": 0, 
  "to": "string", 
  "tranId": "string" 
} 
 
SelectBrokerFutureTransferRes
42.470. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
clientTranId
string
false
none
none


---

## Page 261

sapi-v7.4.md
2024-05-08
261 / 419
Name
Type
Required
Restrictions
Description
from
string
false
none
none
qty
string
false
none
none
time
integer(int64)
false
none
none
to
string
false
none
none
tranId
string
false
none
none
SelectBrokerSubBnbBurnStatusResp
{ 
  "interestBNBBurn": true, 
  "spotBNBBurn": true, 
  "subAccountId": 0 
} 
 
SelectBrokerSubBnbBurnStatusResp
42.471. Properties
Name
Type
Required
Restrictions
Description
interestBNBBurn
boolean
true
none
spotinterestBNBBurnBNBBurn
spotBNBBurn
boolean
true
none
spotBNBBurn
subAccountId
integer(int64)
true
none
经销商⼦账户id
SelectSpotBnbBurnStatusResp
{ 
  "interestBNBBurn": true, 
  "spotBNBBurn": true 
} 
 
SelectSpotBnbBurnStatusResp
42.472. Properties
Name
Type
Required
Restrictions
Description
interestBNBBurn
boolean
true
none
margin折扣
spotBNBBurn
boolean
true
none
spotBNBBurn
SelectSubAccountFutureTransferRes
{ 
  "asset": "string", 
  "from": "string", 
  "qty": "string", 
  "time": 0, 
  "to": "string", 
  "tranId": 0 
} 
 
SelectSubAccountFutureTransferRes
42.473. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
from
string
false
none
none
qty
string
false
none
none


---

## Page 262

sapi-v7.4.md
2024-05-08
262 / 419
Name
Type
Required
Restrictions
Description
time
integer(int64)
false
none
none
to
string
false
none
none
tranId
integer(int64)
false
none
none
SelectSubUserInfoResp
{ 
  "msg": "string", 
  "subAccounts": [ 
    { 
      "activated": true, 
      "createTime": 0, 
      "email": "string", 
      "gAuth": true, 
      "mobile": "string", 
      "status": "disabled" 
    } 
  ], 
  "success": true 
} 
 
SelectSubUserInfoResp
42.474. Properties
Name
Type
Required
Restrictions
Description
msg
string
false
none
none
subAccounts
[SubAccountVo]
false
none
none
success
boolean
false
none
none
SetAutoStakingResp
{ 
  "success": true 
} 
 
SetAutoStakingResp
42.475. Properties
Name
Type
Required
Restrictions
Description
success
boolean
false
none
none
SetAutoSubscribeResp
{ 
  "success": true 
} 
 
SetAutoSubscribeResp
42.476. Properties
Name
Type
Required
Restrictions
Description
success
boolean
false
none
none
SetRedeemOptionResp
{ 
  "success": true 


---

## Page 263

sapi-v7.4.md
2024-05-08
263 / 419
} 
 
SetRedeemOptionResp
42.477. Properties
Name
Type
Required
Restrictions
Description
success
boolean
false
none
none
SetRetailCustomedMarginCallRateForSapiResp
{ 
  "afterMarginCall": 0, 
  "collateralCoin": "string", 
  "customizeTime": 0, 
  "orderId": 0, 
  "preMarginCall": 0 
} 
 
SetRetailCustomedMarginCallRateForSapiResp
42.478. Properties
Name
Type
Required
Restrictions
Description
afterMarginCall
number
false
none
none
collateralCoin
string
false
none
none
customizeTime
integer(int64)
false
none
none
orderId
integer(int64)
false
none
none
preMarginCall
number
false
none
none
SettleCreditOrdersResp
{ 
  "status": "string" 
} 
 
SettleCreditOrdersResp
42.479. Properties
Name
Type
Required
Restrictions
Description
status
string
false
none
none
SettlePriceUpdateResp
{ 
  "code": "string", 
  "fixingPrice": 0, 
  "fixingTime": 0, 
  "message": "string", 
  "quoteAsset": "string", 
  "underlying": "string" 
} 
 
SettlePriceUpdateResp
42.480. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none


---

## Page 264

sapi-v7.4.md
2024-05-08
264 / 419
Name
Type
Required
Restrictions
Description
fixingPrice
number
false
none
none
fixingTime
integer(int64)
false
none
none
message
string
false
none
none
quoteAsset
string
false
none
none
underlying
string
false
none
none
SettlePriceUpdateResultResp
{ 
  "code": "string", 
  "message": "string", 
  "resultList": [ 
    { 
      "code": "string", 
      "fixingPrice": 0, 
      "fixingTime": 0, 
      "message": "string", 
      "quoteAsset": "string", 
      "underlying": "string" 
    } 
  ] 
} 
 
SettlePriceUpdateResultResp
42.481. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
message
string
false
none
none
resultList
[SettlePriceUpdateResp]
false
none
none
SettlementPriceV2Req
{ 
  "fixingPrice": 0, 
  "fixingTime": 0, 
  "quoteAsset": "string", 
  "timestamp": 0, 
  "underlying": "string" 
} 
 
SettlementPriceV2Req
42.482. Properties
Name
Type
Required
Restrictions
Description
fixingPrice
number
false
none
none
fixingTime
integer(int64)
false
none
none
quoteAsset
string
false
none
none
timestamp
integer(int64)
false
none
none
underlying
string
false
none
none
Share
{ 
  "asset": { 
    "property1": 0, 
    "property2": 0 
  }, 


---

## Page 265

sapi-v7.4.md
2024-05-08
265 / 419
  "shareAmount": 0, 
  "sharePercentage": 0 
} 
 
Share
42.483. Properties
Name
Type
Required
Restrictions
Description
asset
object
false
none
none
» additionalProperties
number
false
none
none
shareAmount
number
false
none
none
sharePercentage
number
false
none
none
SinglePositionAmountDto
{ 
  "amount": 0, 
  "amountInBTC": 0, 
  "amountInUSDT": 0, 
  "asset": "string", 
  "lendingType": "ADDITIONAL" 
} 
 
SinglePositionAmountDto
42.484. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
amountInBTC
number
false
none
none
amountInUSDT
number
false
none
none
asset
string
false
none
none
lendingType
string
false
none
none
42.484.1. Enumerated Values
Property
Value
lendingType
ADDITIONAL
lendingType
CUSTOMIZED_FIXED
lendingType
DAILY
lendingType
EXPERIENCE_COUPON
lendingType
REAL_TIME
lendingType
REGULAR
lendingType
SUPER_MINING
SpotMarginInterestBnbBurnSwitchResp
{ 
  "interestBNBBurn": true, 
  "spotBNBBurn": true 
} 
 
SpotMarginInterestBnbBurnSwitchResp
42.485. Properties


---

## Page 266

sapi-v7.4.md
2024-05-08
266 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
interestBNBBurn
boolean
true
none
margin-bnb折扣
spotBNBBurn
boolean
true
none
现货bnb燃烧
SpotSubUserAssetBtcVo
{ 
  "email": "string", 
  "totalAsset": 0 
} 
 
SpotSubUserAssetBtcVo
42.486. Properties
Name
Type
Required
Restrictions
Description
email
string
false
none
none
totalAsset
number
false
none
none
StakePreviewSapiDto
{ 
  "baseAmt": 0, 
  "baseAsset": "string", 
  "fee": 0, 
  "price": 0, 
  "quoteAmt": 0, 
  "quoteAsset": "string", 
  "share": 0, 
  "slippage": 0 
} 
 
StakePreviewSapiDto
42.487. Properties
Name
Type
Required
Restrictions
Description
baseAmt
number
false
none
none
baseAsset
string
false
none
none
fee
number
false
none
none
price
number
false
none
none
quoteAmt
number
false
none
none
quoteAsset
string
false
none
none
share
number
false
none
none
slippage
number
false
none
none
StakeResponse
{ 
  "success": true 
} 
 
StakeResponse
42.488. Properties
Name
Type
Required
Restrictions
Description
success
boolean
false
none
none


---

## Page 267

sapi-v7.4.md
2024-05-08
267 / 419
StakeV2Response
{ 
  "conversionRatio": "string", 
  "success": true, 
  "wbethAmount": 0 
} 
 
StakeV2Response
42.489. Properties
Name
Type
Required
Restrictions
Description
conversionRatio
string
false
none
none
success
boolean
false
none
none
wbethAmount
number
false
none
none
StakingAccountResp
{ 
  "dotSlotAuction": { 
    "totalAmountInBTC": 0, 
    "totalAmountInUSDT": 0 
  }, 
  "eth2": { 
    "cumulativeProfitInBETH": 0, 
    "lastDayProfitInBETH": 0 
  }, 
  "flexibleDefi": { 
    "lastDayProfitInBTC": 0, 
    "lastDayProfitInUSDT": 0, 
    "totalAmountInBTC": 0, 
    "totalAmountInUSDT": 0 
  }, 
  "lockedDefi": { 
    "lastDayProfitInBTC": 0, 
    "lastDayProfitInUSDT": 0, 
    "totalAmountInBTC": 0, 
    "totalAmountInUSDT": 0 
  }, 
  "totalLastDayProfitInBTC": 0, 
  "totalLastDayProfitInUSDT": 0, 
  "totalStakingAmountInBTC": 0, 
  "totalStakingAmountInUSDT": 0 
} 
 
StakingAccountResp
42.490. Properties
Name
Type
Required
Restrictions
Description
dotSlotAuction
DotAccount
false
none
none
eth2
Eth2Account
false
none
none
flexibleDefi
DefiFlexibleAccount
false
none
none
lockedDefi
DefiLockedAccount
false
none
none
totalLastDayProfitInBTC
number
false
none
none
totalLastDayProfitInUSDT
number
false
none
none
totalStakingAmountInBTC
number
false
none
none
totalStakingAmountInUSDT
number
false
none
none
StakingHistory


---

## Page 268

sapi-v7.4.md
2024-05-08
268 / 419
{ 
  "amount": 0, 
  "asset": "string", 
  "conversionRatio": "string", 
  "distributeAmount": 0, 
  "distributeAsset": "string", 
  "status": "string", 
  "time": 0 
} 
 
StakingHistory
42.491. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
conversionRatio
string
false
none
none
distributeAmount
number
false
none
none
distributeAsset
string
false
none
none
status
string
false
none
none
time
integer(int64)
false
none
none
StakingHistoryResponse
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "conversionRatio": "string", 
      "distributeAmount": 0, 
      "distributeAsset": "string", 
      "status": "string", 
      "time": 0 
    } 
  ], 
  "total": 0 
} 
 
StakingHistoryResponse
42.492. Properties
Name
Type
Required
Restrictions
Description
rows
[StakingHistory]
false
none
none
total
integer(int64)
false
none
none
StakingRecordResp
{ 
  "amount": 0, 
  "asset": "string", 
  "deliverDate": 0, 
  "lockPeriod": 0, 
  "position": 0, 
  "positionId": 0, 
  "project": "string", 
  "status": "string", 
  "time": 0, 
  "type": "string" 
} 
 


---

## Page 269

sapi-v7.4.md
2024-05-08
269 / 419
StakingRecordResp
42.493. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
deliverDate
integer(int64)
false
none
none
lockPeriod
integer(int32)
false
none
none
position
number
false
none
none
positionId
integer(int64)
false
none
none
project
string
false
none
none
status
string
false
none
none
time
integer(int64)
false
none
none
type
string
false
none
none
StatusResp
{ 
  "data": {} 
} 
 
StatusResp
42.494. Properties
Name
Type
Required
Restrictions
Description
data
object
false
none
none
StatusUpdateResult
{ 
  "advNo": "string", 
  "errorCode": "string", 
  "errorMsg": "string" 
} 
 
StatusUpdateResult
42.495. Properties
Name
Type
Required
Restrictions
Description
advNo
string
false
none
Adv no
errorCode
string
false
none
Error code
errorMsg
string
false
none
Error message
StoreAddressVo
{ 
  "building": "string", 
  "city": "string", 
  "country": "string", 
  "flat": "string", 
  "floor": "string", 
  "province": "string", 
  "remark": "string", 
  "street": "string", 
  "zipCode": "string" 
} 
 


---

## Page 270

sapi-v7.4.md
2024-05-08
270 / 419
StoreAddressVo
42.496. Properties
Name
Type
Required
Restrictions
Description
building
string
false
none
none
city
string
false
none
none
country
string
false
none
none
flat
string
false
none
none
floor
string
false
none
none
province
string
false
none
none
remark
string
false
none
none
street
string
false
none
none
zipCode
string
false
none
none
StoreMaterialItemVo
{ 
  "dataFrom": "string", 
  "dataType": "string", 
  "fileType": "string", 
  "id": 0, 
  "itemData": "string", 
  "itemIdentifier": "string", 
  "storeId": 0 
} 
 
StoreMaterialItemVo
42.497. Properties
Name
Type
Required
Restrictions
Description
dataFrom
string
false
none
数据来源-operator
dataType
string
false
none
数据类型-text,video,image
fileType
string
false
none
⽂件类型-mp4,jpg
id
integer(int64)
false
none
ID
itemData
string
false
none
申请条⽬数据-file path
itemIdentifier
string
false
none
申请材料条⽬标志:STORE_OWNERSHIP_PROOF,STORE_SURROUNDINGS
storeId
integer(int64)
false
none
storeId
StoreVo
{ 
  "applyStatus": 0, 
  "availableMargin": 0, 
  "countryCode": "string", 
  "distance": 0, 
  "enable": "string", 
  "fineAmount": 0, 
  "friOpenTime": "string", 
  "friOpenTimeLocal": "string", 
  "fullAddress": "string", 
  "geoCode": "string", 
  "latitude": 0, 
  "longitude": 0, 
  "margin": 0, 
  "marginFreeze": 0, 
  "marginUnit": "string", 
  "monOpenTime": "string", 
  "monOpenTimeLocal": "string", 
  "processingAmount": 0, 
  "refundProcessingAmount": 0, 


---

## Page 271

sapi-v7.4.md
2024-05-08
271 / 419
  "refundableFineAmount": 0, 
  "remark": "string", 
  "satOpenTime": "string", 
  "satOpenTimeLocal": "string", 
  "status": 0, 
  "storeAddressVo": { 
    "building": "string", 
    "city": "string", 
    "country": "string", 
    "flat": "string", 
    "floor": "string", 
    "province": "string", 
    "remark": "string", 
    "street": "string", 
    "zipCode": "string" 
  }, 
  "storeId": 0, 
  "storeMaterialItemVoList": [ 
    { 
      "dataFrom": "string", 
      "dataType": "string", 
      "fileType": "string", 
      "id": 0, 
      "itemData": "string", 
      "itemIdentifier": "string", 
      "storeId": 0 
    } 
  ], 
  "storeName": "string", 
  "storeShortName": "string", 
  "submissionTime": "2019-08-24T14:15:22Z", 
  "sunOpenTime": "string", 
  "sunOpenTimeLocal": "string", 
  "thuOpenTime": "string", 
  "thuOpenTimeLocal": "string", 
  "timeZone": "string", 
  "tueOpenTime": "string", 
  "tueOpenTimeLocal": "string", 
  "updateTime": "2019-08-24T14:15:22Z", 
  "userId": 0, 
  "valid": true, 
  "wedOpenTime": "string", 
  "wedOpenTimeLocal": "string" 
} 
 
StoreVo
42.498. Properties
Name
Type
Required
Restrictions
Description
applyStatus
integer(int32)
false
none
1,申请提交APPLICATION_APPLY 2,申请通过APPLICATION_PASS 3,申请拒绝APPLICA
APPLICATION_DELETE
availableMargin
number
false
none
可⽤保证⾦ available Margin = Margin - fine - freeze
countryCode
string
false
none
none
distance
number
false
none
distance , unit:meter
enable
string
false
none
none
fineAmount
number
false
none
none
friOpenTime
string
false
none
none
friOpenTimeLocal
string
false
none
none
fullAddress
string
false
none
none
geoCode
string
false
none
none
latitude
number
false
none
none
longitude
number
false
none
none
margin
number
false
none
none
marginFreeze
number
false
none
none
marginUnit
string
false
none
none


---

## Page 272

sapi-v7.4.md
2024-05-08
272 / 419
Name
Type
Required
Restrictions
Description
monOpenTime
string
false
none
00000000000000000000000000000000000000000000000000000000000000
total 96 bit. one bit for 15 minutes
monOpenTimeLocal
string
false
none
none
processingAmount
number
false
none
none
refundProcessingAmount
number
false
none
none
refundableFineAmount
number
false
none
none
remark
string
false
none
none
satOpenTime
string
false
none
none
satOpenTimeLocal
string
false
none
none
status
integer(int32)
false
none
0:offline 1：online 2:close
storeAddressVo
StoreAddressVo
false
none
none
storeId
integer(int64)
false
none
storeId
storeMaterialItemVoList
[StoreMaterialItemVo]
false
none
store's pictures and images and videos
storeName
string
false
none
none
storeShortName
string
false
none
none
submissionTime
string(date-time)
false
none
none
sunOpenTime
string
false
none
none
sunOpenTimeLocal
string
false
none
none
thuOpenTime
string
false
none
none
thuOpenTimeLocal
string
false
none
none
timeZone
string
false
none
none
tueOpenTime
string
false
none
00000000000000000000000000000000000000000000000000000000000000
total 96 bit. one bit for 15 minutes
tueOpenTimeLocal
string
false
none
none
updateTime
string(date-time)
false
none
none
userId
integer(int64)
false
none
none
valid
boolean
false
none
none
wedOpenTime
string
false
none
00000000000000000000000000000000000000000000000000000000000000
total 96 bit. one bit for 15 minutes
wedOpenTimeLocal
string
false
none
none
SubAccountAssetResp
{ 
  "data": [ 
    {} 
  ], 
  "timestamp": 0 
} 
 
SubAccountAssetResp
42.499. Properties
Name
Type
Required
Restrictions
Description
data
[object]
false
none
⼦账户资产列表
timestamp
integer(int64)
false
none
查询时间（UTC）
SubAccountBriefVo
{ 
  "createTime": "2019-08-24T14:15:22Z", 


---

## Page 273

sapi-v7.4.md
2024-05-08
273 / 419
  "email": "string", 
  "isAssetManagementSubAccount": true, 
  "isFreeze": true, 
  "isManagedSubAccount": true 
} 
 
SubAccountBriefVo
42.500. Properties
Name
Type
Required
Restrictions
Description
createTime
string(date-time)
false
none
none
email
string
false
none
none
isAssetManagementSubAccount
boolean
false
none
none
isFreeze
boolean
false
none
none
isManagedSubAccount
boolean
false
none
none
SubAccountCustodialBindingSyncResp
{ 
  "code": 0, 
  "data": true, 
  "message": "string" 
} 
 
SubAccountCustodialBindingSyncResp
42.501. Properties
Name
Type
Required
Restrictions
Description
code
integer(int32)
false
none
none
data
boolean
false
none
none
message
string
false
none
none
SubAccountDepositHistResp
{ 
  "address": "string", 
  "addressTag": "string", 
  "amount": 0, 
  "coin": "string", 
  "confirmTimes": "string", 
  "depositId": 0, 
  "insertTime": 0, 
  "network": "string", 
  "selfReturnStatus": 0, 
  "sourceAddress": "string", 
  "status": 0, 
  "subAccountId": "string", 
  "txId": "string" 
} 
 
SubAccountDepositHistResp
42.502. Properties
Name
Type
Required
Restrictions
Description
address
string
false
none
none
addressTag
string
false
none
none
amount
number
false
none
none
coin
string
false
none
none


---

## Page 274

sapi-v7.4.md
2024-05-08
274 / 419
Name
Type
Required
Restrictions
Description
confirmTimes
string
false
none
none
depositId
integer(int64)
false
none
none
insertTime
integer(int64)
false
none
none
network
string
false
none
none
selfReturnStatus
integer(int32)
false
none
none
sourceAddress
string
false
none
none
status
integer(int32)
false
none
none
subAccountId
string
false
none
none
txId
string
false
none
none
SubAccountFutureTransferRes
{ 
  "success": true, 
  "txnId": 0 
} 
 
SubAccountFutureTransferRes
42.503. Properties
Name
Type
Required
Restrictions
Description
success
boolean
false
none
none
txnId
integer(int64)
false
none
none
SubAccountFuturesAssetResp
{ 
  "futuresEnable": true, 
  "subAccountId": "string", 
  "totalInitialMarginOfUsdt": "string", 
  "totalMaintenanceMarginOfUsdt": "string", 
  "totalMarginBalanceOfUsdt": "string", 
  "totalOpenOrderInitialMarginOfUsdt": "string", 
  "totalPositionInitialMarginOfUsdt": "string", 
  "totalUnrealizedProfitOfUsdt": "string", 
  "totalWalletBalanceOfUsdt": "string" 
} 
 
SubAccountFuturesAssetResp
42.504. Properties
Name
Type
Required
Restrictions
Description
futuresEnable
boolean
false
none
是否开通futures
subAccountId
string
false
none
经销商⼦账户id
totalInitialMarginOfUsdt
string
false
none
起始保证⾦（单位：USDT）
totalMaintenanceMarginOfUsdt
string
false
none
维持保证⾦（单位：USDT）
totalMarginBalanceOfUsdt
string
false
none
保证⾦余额（单位：USDT）
totalOpenOrderInitialMarginOfUsdt
string
false
none
挂单起始保证⾦（单位：USDT）
totalPositionInitialMarginOfUsdt
string
false
none
持仓起始保证⾦（单位：USDT）
totalUnrealizedProfitOfUsdt
string
false
none
持仓未实现盈亏（单位：USDT）
totalWalletBalanceOfUsdt
string
false
none
钱包余额（单位：USDT）
SubAccountFuturesEnableResp


---

## Page 275

sapi-v7.4.md
2024-05-08
275 / 419
{ 
  "email": "string", 
  "isFuturesEnabled": true 
} 
 
SubAccountFuturesEnableResp
42.505. Properties
Name
Type
Required
Restrictions
Description
email
string
false
none
⼦账户邮箱
isFuturesEnabled
boolean
false
none
是否启⽤futures
SubAccountMarginAssetResp
{ 
  "marginEnable": true, 
  "marginLevel": "string", 
  "subAccountId": "string", 
  "totalAssetOfBtc": "string", 
  "totalLiabilityOfBtc": "string", 
  "totalNetAssetOfBtc": "string" 
} 
 
SubAccountMarginAssetResp
42.506. Properties
Name
Type
Required
Restrictions
Description
marginEnable
boolean
false
none
是否开通margin
marginLevel
string
false
none
⻛险率
subAccountId
string
false
none
⼦账户ID
totalAssetOfBtc
string
false
none
总资产（单位：BTC）
totalLiabilityOfBtc
string
false
none
总负债（单位：BTC）
totalNetAssetOfBtc
string
false
none
净资产（单位：BTC）
SubAccountMarginEnableResp
{ 
  "email": "string", 
  "isMarginEnabled": true 
} 
 
SubAccountMarginEnableResp
42.507. Properties
Name
Type
Required
Restrictions
Description
email
string
false
none
⼦账户邮箱
isMarginEnabled
boolean
false
none
是否启⽤margin
SubAccountSignLVTResp
{ 
  "enableBlvt": true, 
  "subAccountId": "string" 
} 
 


---

## Page 276

sapi-v7.4.md
2024-05-08
276 / 419
SubAccountSignLVTResp
42.508. Properties
Name
Type
Required
Restrictions
Description
enableBlvt
boolean
false
none
none
subAccountId
string
false
none
none
SubAccountSpotAssetResp
{ 
  "subAccountId": "string", 
  "totalBalanceOfBtc": "string" 
} 
 
SubAccountSpotAssetResp
42.509. Properties
Name
Type
Required
Restrictions
Description
subAccountId
string
false
none
⼦账户ID
totalBalanceOfBtc
string
false
none
总资产（单位：BTC）
SubAccountVo
{ 
  "activated": true, 
  "createTime": 0, 
  "email": "string", 
  "gAuth": true, 
  "mobile": "string", 
  "status": "disabled" 
} 
 
SubAccountVo
42.510. Properties
Name
Type
Required
Restrictions
Description
activated
boolean
false
none
none
createTime
integer(int64)
false
none
none
email
string
false
none
none
gAuth
boolean
false
none
none
mobile
string
false
none
none
status
string
false
none
none
42.510.1. Enumerated Values
Property
Value
status
disabled
status
enabled
SubUserFutureAccountResp
{ 
  "deliveryAccountResp": { 
    "assets": [ 
      { 
        "asset": "string", 
        "initialMargin": "string", 
        "maintenanceMargin": "string", 


---

## Page 277

sapi-v7.4.md
2024-05-08
277 / 419
        "marginBalance": "string", 
        "maxWithdrawAmount": "string", 
        "openOrderInitialMargin": "string", 
        "positionInitialMargin": "string", 
        "unrealizedProfit": "string", 
        "updateTime": 0, 
        "walletBalance": "string" 
      } 
    ], 
    "canDeposit": true, 
    "canTrade": true, 
    "canWithdraw": true, 
    "email": "string", 
    "feeTier": 0, 
    "updateTime": 0 
  }, 
  "futureAccountResp": { 
    "asset": "string", 
    "assets": [ 
      { 
        "asset": "string", 
        "initialMargin": "string", 
        "maintenanceMargin": "string", 
        "marginBalance": "string", 
        "maxWithdrawAmount": "string", 
        "openOrderInitialMargin": "string", 
        "positionInitialMargin": "string", 
        "unrealizedProfit": "string", 
        "updateTime": 0, 
        "walletBalance": "string" 
      } 
    ], 
    "canDeposit": true, 
    "canTrade": true, 
    "canWithdraw": true, 
    "email": "string", 
    "feeTier": 0, 
    "maxWithdrawAmount": "string", 
    "totalInitialMargin": "string", 
    "totalMaintenanceMargin": "string", 
    "totalMarginBalance": "string", 
    "totalOpenOrderInitialMargin": "string", 
    "totalPositionInitialMargin": "string", 
    "totalUnrealizedProfit": "string", 
    "totalWalletBalance": "string", 
    "updateTime": 0 
  } 
} 
 
SubUserFutureAccountResp
42.511. Properties
Name
Type
Required
Restrictions
Description
deliveryAccountResp
QuerySubAccountDeliveryAccountResp
false
none
币本位合约账户详情
futureAccountResp
QuerySubAccountFutureAccountResp
false
none
U本位合约账户详情
SubUserFutureAccountSummaryResp
{ 
  "deliveryAccountSummaryResp": { 
    "asset": "string", 
    "subAccountList": [ 
      { 
        "asset": "string", 
        "email": "string", 
        "totalMarginBalance": "string", 
        "totalUnrealizedProfit": "string", 
        "totalWalletBalance": "string" 
      } 
    ], 
    "totalMarginBalanceOfBTC": "string", 
    "totalUnrealizedProfitOfBTC": "string", 
    "totalWalletBalanceOfBTC": "string" 
  }, 


---

## Page 278

sapi-v7.4.md
2024-05-08
278 / 419
  "futureAccountSummaryResp": { 
    "asset": "string", 
    "subAccountList": [ 
      { 
        "asset": "string", 
        "email": "string", 
        "totalInitialMargin": "string", 
        "totalMaintenanceMargin": "string", 
        "totalMarginBalance": "string", 
        "totalOpenOrderInitialMargin": "string", 
        "totalPositionInitialMargin": "string", 
        "totalUnrealizedProfit": "string", 
        "totalWalletBalance": "string" 
      } 
    ], 
    "totalInitialMargin": "string", 
    "totalMaintenanceMargin": "string", 
    "totalMarginBalance": "string", 
    "totalOpenOrderInitialMargin": "string", 
    "totalPositionInitialMargin": "string", 
    "totalUnrealizedProfit": "string", 
    "totalWalletBalance": "string" 
  } 
} 
 
SubUserFutureAccountSummaryResp
42.512. Properties
Name
Type
Required
Restrictions
Description
deliveryAccountSummaryResp
QueryDeliveryAccountSummaryResp
false
none
币本位合约资产信息总览
futureAccountSummaryResp
QueryFuturesAccountSummaryResp
false
none
U本位合约资产信息汇总览
SubUserFuturePositionRiskResp
{ 
  "deliveryPositionRiskVOS": [ 
    { 
      "entryPrice": "string", 
      "isAutoAddMargin": "string", 
      "isolated": "string", 
      "isolatedMargin": "string", 
      "isolatedWallet": "string", 
      "leverage": "string", 
      "markPrice": "string", 
      "positionAmount": "string", 
      "positionSide": "string", 
      "symbol": "string", 
      "unrealizedProfit": "string" 
    } 
  ], 
  "futurePositionRiskVOS": [ 
    { 
      "entryPrice": "string", 
      "leverage": "string", 
      "liquidationPrice": "string", 
      "markPrice": "string", 
      "maxNotional": "string", 
      "positionAmount": "string", 
      "symbol": "string", 
      "unrealizedProfit": "string" 
    } 
  ] 
} 
 
SubUserFuturePositionRiskResp
42.513. Properties
Name
Type
Required
Restrictions
Description
deliveryPositionRiskVOS
[DeliveryPositionRiskVO]
false
none
none


---

## Page 279

sapi-v7.4.md
2024-05-08
279 / 419
Name
Type
Required
Restrictions
Description
futurePositionRiskVOS
[FuturePositionRiskVO]
false
none
none
SubUserInfoVoForSapiVersion
{ 
  "email": "string", 
  "insertTime": "2019-08-24T14:15:22Z", 
  "isFutureEnabled": true, 
  "isMarginEnabled": true, 
  "isSubUserEnabled": true, 
  "isUserActive": true, 
  "mobile": "string" 
} 
 
SubUserInfoVoForSapiVersion
42.514. Properties
Name
Type
Required
Restrictions
Description
email
string
false
none
⼦账户邮箱
insertTime
string(date-time)
false
none
⼦账户注册时间
isFutureEnabled
boolean
false
none
是否启⽤future
isMarginEnabled
boolean
false
none
是否启⽤margin
isSubUserEnabled
boolean
false
none
是否启⽤⼦账户
isUserActive
boolean
false
none
是否激活
mobile
string
false
none
⼦账户绑定的⼿机号
SubUserTradeInfoVo
{ 
  "btc": 0, 
  "btcFutures": 0, 
  "btcMargin": 0, 
  "busd": 0, 
  "busdFutures": 0, 
  "busdMargin": 0, 
  "date": 0, 
  "userId": 0 
} 
 
SubUserTradeInfoVo
42.515. Properties
Name
Type
Required
Restrictions
Description
btc
number
false
none
⽤户折算BTC交易量
btcFutures
number
false
none
折算BTC的成交量，期货部分
btcMargin
number
false
none
折算BTC的成交量，杠杆部分
busd
number
false
none
⽤户折算busd交易量
busdFutures
number
false
none
折算busd的成交量，期货部分
busdMargin
number
false
none
折算busd的成交量，杠杆部分
date
integer(int64)
false
none
统计时间戳
userId
integer(int64)
false
none
⽤户Id
SubscriptionPreviewResp
{ 
  "deliverDate": 0, 


---

## Page 280

sapi-v7.4.md
2024-05-08
280 / 419
  "estTotalExtraRewardAmt": 0, 
  "extraRewardAsset": "string", 
  "nextPay": 0, 
  "nextPayDate": 0, 
  "nextSubscriptionDate": 0, 
  "rewardAsset": "string", 
  "rewardsEndDate": 0, 
  "totalRewardAmt": 0, 
  "valueDate": 0 
} 
 
SubscriptionPreviewResp
42.516. Properties
Name
Type
Required
Restrictions
Description
deliverDate
integer(int64)
false
none
none
estTotalExtraRewardAmt
number
false
none
none
extraRewardAsset
string
false
none
none
nextPay
number
false
none
none
nextPayDate
integer(int64)
false
none
none
nextSubscriptionDate
integer(int64)
false
none
none
rewardAsset
string
false
none
none
rewardsEndDate
integer(int64)
false
none
none
totalRewardAmt
number
false
none
none
valueDate
integer(int64)
false
none
none
SubscriptionRecord
{ 
  "amount": 0, 
  "amtFromFunding": 0, 
  "amtFromSpot": 0, 
  "asset": "string", 
  "lockPeriod": 0, 
  "positionId": 0, 
  "projectId": "string", 
  "purchaseId": 0, 
  "sourceAccount": "string", 
  "status": "string", 
  "time": 0, 
  "type": "string" 
} 
 
SubscriptionRecord
42.517. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
amtFromFunding
number
false
none
none
amtFromSpot
number
false
none
none
asset
string
false
none
none
lockPeriod
integer(int32)
false
none
none
positionId
integer(int64)
false
none
none
projectId
string
false
none
none
purchaseId
integer(int64)
false
none
none
sourceAccount
string
false
none
none
status
string
false
none
none


---

## Page 281

sapi-v7.4.md
2024-05-08
281 / 419
Name
Type
Required
Restrictions
Description
time
integer(int64)
false
none
none
type
string
false
none
none
SubscriptionRecordResp
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "amtFromFunding": 0, 
      "amtFromSpot": 0, 
      "asset": "string", 
      "lockPeriod": 0, 
      "positionId": 0, 
      "projectId": "string", 
      "purchaseId": 0, 
      "sourceAccount": "string", 
      "status": "string", 
      "time": 0, 
      "type": "string" 
    } 
  ], 
  "total": 0 
} 
 
SubscriptionRecordResp
42.518. Properties
Name
Type
Required
Restrictions
Description
rows
[SubscriptionRecord]
false
none
none
total
integer(int64)
false
none
none
SubscriptionResp
{ 
  "positionId": 0, 
  "purchaseId": 0, 
  "success": true 
} 
 
SubscriptionResp
42.519. Properties
Name
Type
Required
Restrictions
Description
positionId
integer(int64)
false
none
none
purchaseId
integer(int64)
false
none
none
success
boolean
false
none
none
SuccessResp
{ 
  "msg": "string" 
} 
 
SuccessResp
42.520. Properties
Name
Type
Required
Restrictions
Description


---

## Page 282

sapi-v7.4.md
2024-05-08
282 / 419
Name
Type
Required
Restrictions
Description
msg
string
false
none
none
SwapHistoryResp
{ 
  "baseAsset": "string", 
  "baseQty": 0, 
  "fee": 0, 
  "price": 0, 
  "quoteAsset": "string", 
  "quoteQty": 0, 
  "status": 0, 
  "swapId": 0, 
  "swapTime": 0 
} 
 
SwapHistoryResp
42.521. Properties
Name
Type
Required
Restrictions
Description
baseAsset
string
false
none
none
baseQty
number
false
none
none
fee
number
false
none
none
price
number
false
none
none
quoteAsset
string
false
none
none
quoteQty
number
false
none
none
status
integer(int32)
false
none
none
swapId
integer(int64)
false
none
none
swapTime
integer(int64)
false
none
none
SwapLiquidityAddResp
{ 
  "operationId": 0 
} 
 
SwapLiquidityAddResp
42.522. Properties
Name
Type
Required
Restrictions
Description
operationId
integer(int64)
false
none
none
SwapLiquidityOpsResp
{ 
  "liquidityAmount": [ 
    { 
      "amount": 0, 
      "asset": "string" 
    } 
  ], 
  "operation": "string", 
  "operationId": 0, 
  "poolId": 0, 
  "poolName": "string", 
  "shareAmount": 0, 
  "status": 0, 
  "updateTime": 0 
} 
 


---

## Page 283

sapi-v7.4.md
2024-05-08
283 / 419
SwapLiquidityOpsResp
42.523. Properties
Name
Type
Required
Restrictions
Description
liquidityAmount
[LiquidityAmount]
false
none
none
operation
string
false
none
none
operationId
integer(int64)
false
none
none
poolId
integer(int64)
false
none
none
poolName
string
false
none
none
shareAmount
number
false
none
none
status
integer(int32)
false
none
none
updateTime
integer(int64)
false
none
none
SwapLiquidityRemoveResp
{ 
  "operationId": 0 
} 
 
SwapLiquidityRemoveResp
42.524. Properties
Name
Type
Required
Restrictions
Description
operationId
integer(int64)
false
none
none
SwapLiquidityResp
{ 
  "liquidity": { 
    "property1": 0, 
    "property2": 0 
  }, 
  "poolId": 0, 
  "poolName": "string", 
  "share": { 
    "asset": { 
      "property1": 0, 
      "property2": 0 
    }, 
    "shareAmount": 0, 
    "sharePercentage": 0 
  }, 
  "updateTime": 0 
} 
 
SwapLiquidityResp
42.525. Properties
Name
Type
Required
Restrictions
Description
liquidity
object
false
none
none
» additionalProperties
number
false
none
none
poolId
integer(int64)
false
none
none
poolName
string
false
none
none
share
Share
false
none
none
updateTime
integer(int64)
false
none
none


---

## Page 284

sapi-v7.4.md
2024-05-08
284 / 419
SwapPoolResp
{ 
  "assets": [ 
    "string" 
  ], 
  "poolId": 0, 
  "poolName": "string" 
} 
 
SwapPoolResp
42.526. Properties
Name
Type
Required
Restrictions
Description
assets
[string]
false
none
币种
poolId
integer(int64)
false
none
none
poolName
string
false
none
池名称
SwapQuotesResp
{ 
  "baseAsset": "string", 
  "baseQty": 0, 
  "fee": 0, 
  "price": 0, 
  "quoteAsset": "string", 
  "quoteQty": 0, 
  "slippage": 0 
} 
 
SwapQuotesResp
42.527. Properties
Name
Type
Required
Restrictions
Description
baseAsset
string
false
none
none
baseQty
number
false
none
none
fee
number
false
none
none
price
number
false
none
none
quoteAsset
string
false
none
none
quoteQty
number
false
none
none
slippage
number
false
none
none
SwapSubmitResp
{ 
  "swapId": 0 
} 
 
SwapSubmitResp
42.528. Properties
Name
Type
Required
Restrictions
Description
swapId
integer(int64)
false
none
none
SwapTradeVolResp


---

## Page 285

sapi-v7.4.md
2024-05-08
285 / 419
{ 
  "rows": [ 
    { 
      "baseAsset": "string", 
      "baseVol": "string", 
      "poolId": "string", 
      "poolName": "string", 
      "quoteAsset": "string", 
      "quoteVol": "string" 
    } 
  ], 
  "total": 0 
} 
 
SwapTradeVolResp
42.529. Properties
Name
Type
Required
Restrictions
Description
rows
[PoolVolume]
false
none
none
total
integer(int64)
false
none
none
SystemStatusResp
{ 
  "msg": "string", 
  "status": 0 
} 
 
SystemStatusResp
42.530. Properties
Name
Type
Required
Restrictions
Description
msg
string
false
none
none
status
integer(int32)
false
none
none
TaxRebateDetailVo
{ 
  "amount": 0, 
  "asset": "string", 
  "type": 0, 
  "updateTime": "2019-08-24T14:15:22Z" 
} 
 
TaxRebateDetailVo
42.531. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
type
integer(int32)
false
none
none
updateTime
string(date-time)
false
none
none
ThirdDipositHistory
{ 
  "contractAdrress": "string", 
  "network": "string", 
  "timestamp": "2019-08-24T14:15:22Z", 


---

## Page 286

sapi-v7.4.md
2024-05-08
286 / 419
  "tokenId": "string", 
  "txID": "string" 
} 
 
ThirdDipositHistory
42.532. Properties
Name
Type
Required
Restrictions
Description
contractAdrress
string
false
none
none
network
string
false
none
none
timestamp
string(date-time)
false
none
none
tokenId
string
false
none
none
txID
string
false
none
none
ThirdNftInfo
{ 
  "contractAddress": "string", 
  "network": "string", 
  "tokenId": "string" 
} 
 
ThirdNftInfo
42.533. Properties
Name
Type
Required
Restrictions
Description
contractAddress
string
false
none
none
network
string
false
none
none
tokenId
string
false
none
none
ThirdPartyNftAssetVo
{ 
  "assetStatus": "string", 
  "assetType": "string", 
  "brandingId": 0, 
  "brandingName": "string", 
  "buyOutPrice": 0, 
  "collectionId": 0, 
  "collectionName": "string", 
  "contractAddress": "string", 
  "creatorName": "string", 
  "currency": "string", 
  "expireDate": 0, 
  "itemTypeId": 0, 
  "itemTypeName": "string", 
  "listingOrderNumber": 0, 
  "nftInfoId": 0, 
  "orderType": "string", 
  "ownerName": "string", 
  "productId": 0, 
  "rarity": "string", 
  "startingPrice": 0, 
  "tokenId": "string" 
} 
 
ThirdPartyNftAssetVo
42.534. Properties
Name
Type
Required
Restrictions
Description


---

## Page 287

sapi-v7.4.md
2024-05-08
287 / 419
Name
Type
Required
Restrictions
Description
assetStatus
string(byte)
false
none
none
assetType
string(byte)
false
none
none
brandingId
integer(int64)
false
none
none
brandingName
string
false
none
none
buyOutPrice
number
false
none
none
collectionId
integer(int64)
false
none
none
collectionName
string
false
none
none
contractAddress
string
false
none
none
creatorName
string
false
none
none
currency
string
false
none
none
expireDate
integer(int64)
false
none
none
itemTypeId
integer(int64)
false
none
none
itemTypeName
string
false
none
none
listingOrderNumber
integer(int64)
false
none
none
nftInfoId
integer(int64)
false
none
none
orderType
string(byte)
false
none
none
ownerName
string
false
none
none
productId
integer(int64)
false
none
none
rarity
string(byte)
false
none
none
startingPrice
number
false
none
none
tokenId
string
false
none
none
ThirdTokenAddress
{ 
  "contractAddress": "string", 
  "network": "string", 
  "tokenId": "string" 
} 
 
ThirdTokenAddress
42.535. Properties
Name
Type
Required
Restrictions
Description
contractAddress
string
false
none
none
network
string
false
none
none
tokenId
string
false
none
none
ThirdTradeHistory
{ 
  "orderNo": "string", 
  "tokens": [ 
    { 
      "contractAddress": "string", 
      "network": "string", 
      "tokenId": "string" 
    } 
  ], 
  "tradeAmount": "string", 
  "tradeCurrency": "string", 
  "tradeRevenue": "string", 
  "tradeTime": "2019-08-24T14:15:22Z" 
} 
 


---

## Page 288

sapi-v7.4.md
2024-05-08
288 / 419
ThirdTradeHistory
42.536. Properties
Name
Type
Required
Restrictions
Description
orderNo
string
false
none
none
tokens
[ThirdTokenAddress]
false
none
none
tradeAmount
string
false
none
none
tradeCurrency
string
false
none
none
tradeRevenue
string
false
none
none
tradeTime
string(date-time)
false
none
none
ThirdTradeOnSaleDto
{ 
  "nftId": 0, 
  "productId": 0 
} 
 
ThirdTradeOnSaleDto
42.537. Properties
Name
Type
Required
Restrictions
Description
nftId
integer(int64)
false
none
none
productId
integer(int64)
false
none
none
ThirdWithdrawOrder
{ 
  "contractAdrress": "string", 
  "fee": 0, 
  "feeAsset": "string", 
  "network": "string", 
  "timestamp": "2019-08-24T14:15:22Z", 
  "tokenId": "string", 
  "txID": "string" 
} 
 
ThirdWithdrawOrder
42.538. Properties
Name
Type
Required
Restrictions
Description
contractAdrress
string
false
none
none
fee
number
false
none
none
feeAsset
string
false
none
none
network
string
false
none
none
timestamp
string(date-time)
false
none
none
tokenId
string
false
none
none
txID
string
false
none
none
ToCoinList
{ 
  "coin": "string", 
  "fromMax": 0, 
  "fromMin": 0 


---

## Page 289

sapi-v7.4.md
2024-05-08
289 / 419
} 
 
ToCoinList
42.539. Properties
Name
Type
Required
Restrictions
Description
coin
string
false
none
none
fromMax
number
false
none
none
fromMin
number
false
none
none
TradeBaseBatchOnsaleApplyResponse
{ 
  "failSize": 0, 
  "list": [ 
    { 
      "nftId": 0, 
      "productId": 0 
    } 
  ], 
  "successSize": 0 
} 
 
TradeBaseBatchOnsaleApplyResponse
42.540. Properties
Name
Type
Required
Restrictions
Description
failSize
integer(int32)
false
none
none
list
[ThirdTradeOnSaleDto]
false
none
none
successSize
integer(int32)
false
none
none
TradeBaseDepositHistoryResponse
{ 
  "list": [ 
    { 
      "contractAdrress": "string", 
      "network": "string", 
      "timestamp": "2019-08-24T14:15:22Z", 
      "tokenId": "string", 
      "txID": "string" 
    } 
  ], 
  "total": 0 
} 
 
TradeBaseDepositHistoryResponse
42.541. Properties
Name
Type
Required
Restrictions
Description
list
[ThirdDipositHistory]
false
none
none
total
integer(int64)
false
none
none
TradeBaseHistoryResponse
{ 
  "list": [ 
    { 
      "orderNo": "string", 
      "tokens": [ 


---

## Page 290

sapi-v7.4.md
2024-05-08
290 / 419
        { 
          "contractAddress": "string", 
          "network": "string", 
          "tokenId": "string" 
        } 
      ], 
      "tradeAmount": "string", 
      "tradeCurrency": "string", 
      "tradeRevenue": "string", 
      "tradeTime": "2019-08-24T14:15:22Z" 
    } 
  ], 
  "total": 0 
} 
 
TradeBaseHistoryResponse
42.542. Properties
Name
Type
Required
Restrictions
Description
list
[ThirdTradeHistory]
false
none
none
total
integer(int64)
false
none
none
TradeBaseNftResponse
{ 
  "list": [ 
    { 
      "contractAddress": "string", 
      "network": "string", 
      "tokenId": "string" 
    } 
  ], 
  "total": 0 
} 
 
TradeBaseNftResponse
42.543. Properties
Name
Type
Required
Restrictions
Description
list
[ThirdNftInfo]
false
none
none
total
integer(int64)
false
none
none
TradeBaseOrderStatusResponse
{ 
  "orderNosMapStatus": { 
    "property1": {}, 
    "property2": {} 
  } 
} 
 
TradeBaseOrderStatusResponse
42.544. Properties
Name
Type
Required
Restrictions
Description
orderNosMapStatus
object
false
none
none
» additionalProperties
object
false
none
none
TradeBasePurchaseProductResponse


---

## Page 291

sapi-v7.4.md
2024-05-08
291 / 419
{ 
  "requestId": 0 
} 
 
TradeBasePurchaseProductResponse
42.545. Properties
Name
Type
Required
Restrictions
Description
requestId
integer(int64)
false
none
none
TradeBasePurchaseSweepFloorResponse
{ 
  "orderNos": [ 
    0 
  ] 
} 
 
TradeBasePurchaseSweepFloorResponse
42.546. Properties
Name
Type
Required
Restrictions
Description
orderNos
[integer]
false
none
none
TradeBaseWithdrawHistoryResponse
{ 
  "list": [ 
    { 
      "contractAdrress": "string", 
      "fee": 0, 
      "feeAsset": "string", 
      "network": "string", 
      "timestamp": "2019-08-24T14:15:22Z", 
      "tokenId": "string", 
      "txID": "string" 
    } 
  ], 
  "total": 0 
} 
 
TradeBaseWithdrawHistoryResponse
42.547. Properties
Name
Type
Required
Restrictions
Description
list
[ThirdWithdrawOrder]
false
none
none
total
integer(int64)
false
none
none
TradeFeeVO
{ 
  "makerCommission": 0, 
  "symbol": "string", 
  "takerCommission": 0 
} 
 
TradeFeeVO
42.548. Properties


---

## Page 292

sapi-v7.4.md
2024-05-08
292 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
makerCommission
number
false
none
none
symbol
string
false
none
none
takerCommission
number
false
none
none
TradeMethodCommissionRateVo
{ 
  "commissionRate": 0, 
  "tradeMethodIdentifier": "string", 
  "tradeMethodName": "string" 
} 
 
TradeMethodCommissionRateVo
42.549. Properties
Name
Type
Required
Restrictions
Description
commissionRate
number
false
none
交易⽅式对应的费率
tradeMethodIdentifier
string
false
none
交易⽅式identifier
tradeMethodName
string
false
none
交易⽅式多语⾔名称
TradingStatusResp
{ 
  "data": {} 
} 
 
TradingStatusResp
42.550. Properties
Name
Type
Required
Restrictions
Description
data
object
false
none
none
TranIdResp
{ 
  "tranId": 0 
} 
 
TranIdResp
42.551. Properties
Name
Type
Required
Restrictions
Description
tranId
integer(int64)
false
none
none
TransactionDetail
{ 
  "asset": "string", 
  "rebalanceAmount": 0, 
  "rebalanceDirection": "BUY", 
  "transactionDateTime": 0 
} 
 
TransactionDetail


---

## Page 293

sapi-v7.4.md
2024-05-08
293 / 419
42.552. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
rebalanceAmount
number
false
none
none
rebalanceDirection
string
false
none
none
transactionDateTime
integer(int64)
false
none
none
42.552.1. Enumerated Values
Property
Value
rebalanceDirection
BUY
rebalanceDirection
SELL
TransactionStatisticsResponse
{ 
  "recent30BtcFuturesTotal": 0, 
  "recent30BtcMarginTotal": 0, 
  "recent30BtcTotal": 0, 
  "recent30BusdFuturesTotal": 0, 
  "recent30BusdMarginTotal": 0, 
  "recent30BusdTotal": 0, 
  "tradeInfoVos": [ 
    { 
      "btc": 0, 
      "btcFutures": 0, 
      "btcMargin": 0, 
      "busd": 0, 
      "busdFutures": 0, 
      "busdMargin": 0, 
      "date": 0, 
      "userId": 0 
    } 
  ] 
} 
 
TransactionStatisticsResponse
42.553. Properties
Name
Type
Required
Restrictions
Description
recent30BtcFuturesTotal
number
false
none
最近30天合约交易量
recent30BtcMarginTotal
number
false
none
最近30天杠杆交易量
recent30BtcTotal
number
false
none
最近30天现货交易量
recent30BusdFuturesTotal
number
false
none
最近30天Busd合约交易量
recent30BusdMarginTotal
number
false
none
最近30天Busd杠杆交易量
recent30BusdTotal
number
false
none
最近30天Busd现货交易量
tradeInfoVos
[SubUserTradeInfoVo]
false
none
交易量明细
TransferHistoryResp
{ 
  "amount": 0, 
  "asset": "string", 
  "fromSymbol": "string", 
  "status": "string", 
  "timestamp": 0, 
  "toSymbol": "string", 
  "transFrom": "CROSS_MARGIN", 
  "transTo": "CROSS_MARGIN", 
  "transferCounterparty": "string", 
  "txId": 0, 
  "type": "string" 


---

## Page 294

sapi-v7.4.md
2024-05-08
294 / 419
} 
 
TransferHistoryResp
42.554. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
划转⾦额
asset
string
false
none
资产名称
fromSymbol
string
false
none
none
status
string
false
none
状态
timestamp
integer(int64)
false
none
划转时间
toSymbol
string
false
none
none
transFrom
string
false
none
none
transTo
string
false
none
none
transferCounterparty
string
false
none
交易对⼿⽅
txId
integer(int64)
false
none
划转ID
type
string
false
none
划转类型
42.554.1. Enumerated Values
Property
Value
transFrom
CROSS_MARGIN
transFrom
DELIVERY
transFrom
FIAT
transFrom
FUNDING
transFrom
FUTURES
transFrom
ISOLATED_MARGIN
transFrom
MINING
transFrom
MOTHER_SPOT
transFrom
OPTION
transFrom
SPOT
transFrom
SUB_MARGIN
transFrom
SUB_SPOT
transTo
CROSS_MARGIN
transTo
DELIVERY
transTo
FIAT
transTo
FUNDING
transTo
FUTURES
transTo
ISOLATED_MARGIN
transTo
MINING
transTo
MOTHER_SPOT
transTo
OPTION
transTo
SPOT
transTo
SUB_MARGIN
transTo
SUB_SPOT
TransferQueryResp


---

## Page 295

sapi-v7.4.md
2024-05-08
295 / 419
{ 
  "amount": 0, 
  "asset": "string", 
  "clientTag": "string", 
  "fromSymbol": "string", 
  "status": "string", 
  "timestamp": 0, 
  "toSymbol": "string", 
  "transFrom": "string", 
  "transTo": "string", 
  "txId": 0, 
  "type": "BORROW" 
} 
 
TransferQueryResp
42.555. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
clientTag
string
false
none
none
fromSymbol
string
false
none
none
status
string
false
none
none
timestamp
integer(int64)
false
none
none
toSymbol
string
false
none
none
transFrom
string
false
none
none
transTo
string
false
none
none
txId
integer(int64)
false
none
none
type
string
false
none
none
42.555.1. Enumerated Values
Property
Value
type
BORROW
type
BURN_ASSET
type
BURN_LIABILITY
type
CHARGE_ASSET
type
DEDUCT_ASSET
type
FORCE_REPAY
type
LIQUIDATION_POUNDAGE
type
REPAY
type
REPAY_INTEREST_POUNDAGE
type
RISK_TRANSFER_ASSET
type
ROLL_IN
type
ROLL_OUT
type
WRITE_OFF
type
WRITE_OFF_TRANSFER_ASSET
TransferResult
{ 
  "amount": 0, 
  "fromAsset": "string", 
  "operateTime": 0, 
  "serviceChargeAmount": 0, 
  "tranId": 0, 


---

## Page 296

sapi-v7.4.md
2024-05-08
296 / 419
  "transferedAmount": 0 
} 
 
TransferResult
42.556. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
fromAsset
string
false
none
none
operateTime
integer(int64)
false
none
none
serviceChargeAmount
number
false
none
none
tranId
integer(int64)
false
none
none
transferedAmount
number
false
none
none
TransferUserMicroassetsResp
{ 
  "clientId": "string", 
  "totalServiceCharge": 0, 
  "totalTransfered": 0, 
  "transferResult": [ 
    { 
      "amount": 0, 
      "fromAsset": "string", 
      "operateTime": 0, 
      "serviceChargeAmount": 0, 
      "tranId": 0, 
      "transferedAmount": 0 
    } 
  ] 
} 
 
TransferUserMicroassetsResp
42.557. Properties
Name
Type
Required
Restrictions
Description
clientId
string
false
none
none
totalServiceCharge
number
false
none
none
totalTransfered
number
false
none
none
transferResult
[TransferResult]
false
none
none
UnclaimedRewardsResp
{ 
  "details": { 
    "property1": { 
      "property1": 0, 
      "property2": 0 
    }, 
    "property2": { 
      "property1": 0, 
      "property2": 0 
    } 
  }, 
  "totalUnclaimedRewards": { 
    "property1": 0, 
    "property2": 0 
  } 
} 
 
UnclaimedRewardsResp


---

## Page 297

sapi-v7.4.md
2024-05-08
297 / 419
42.558. Properties
Name
Type
Required
Restrictions
Description
details
object
false
none
none
» additionalProperties
object
false
none
none
»» additionalProperties
number
false
none
none
totalUnclaimedRewards
object
false
none
none
» additionalProperties
number
false
none
none
UnionPositionDashboardSummaryDto
{ 
  "positionAmountVos": [ 
    { 
      "amount": 0, 
      "amountInBTC": 0, 
      "amountInUSDT": 0, 
      "asset": "string", 
      "lendingType": "ADDITIONAL" 
    } 
  ], 
  "totalAmountInBTC": 0, 
  "totalAmountInUSDT": 0, 
  "totalFixedAmountInBTC": 0, 
  "totalFixedAmountInUSDT": 0, 
  "totalFlexibleInBTC": 0, 
  "totalFlexibleInUSDT": 0 
} 
 
UnionPositionDashboardSummaryDto
42.559. Properties
Name
Type
Required
Restrictions
Description
positionAmountVos
[SinglePositionAmountDto]
false
none
none
totalAmountInBTC
number
false
none
none
totalAmountInUSDT
number
false
none
none
totalFixedAmountInBTC
number
false
none
none
totalFixedAmountInUSDT
number
false
none
none
totalFlexibleInBTC
number
false
none
none
totalFlexibleInUSDT
number
false
none
none
UnionRedemptionDisplayResp
{ 
  "amount": 0, 
  "asset": "string", 
  "clientRedeemId": "string", 
  "createTime": 0, 
  "interest": 0, 
  "principal": 0, 
  "projectId": "string", 
  "projectName": "string", 
  "startTime": 0, 
  "status": "CREATED", 
  "type": "COLLATERAL" 
} 
 
UnionRedemptionDisplayResp
42.560. Properties
Name
Type
Required
Restrictions
Description


---

## Page 298

sapi-v7.4.md
2024-05-08
298 / 419
Name
Type
Required
Restrictions
Description
amount
number
false
none
赎回：本⾦ + 利息
asset
string
false
none
币种
clientRedeemId
string
false
none
clientRedeemId
createTime
integer(int64)
false
none
赎回时间
interest
number
false
none
利息
principal
number
false
none
本⾦
projectId
string
false
none
项⽬ID
projectName
string
false
none
项⽬名称
startTime
integer(int64)
false
none
项⽬开始时间/记息时间
status
string
false
none
赎回状态
type
string
false
none
赎回类型
42.560.1. Enumerated Values
Property
Value
status
CREATED
status
FAILED
status
PAID
type
COLLATERAL
type
FAST
type
NORMAL
UniversalTransferHistoryInfoVo
{ 
  "amount": 0, 
  "asset": "string", 
  "clientTranId": "string", 
  "createTimeStamp": 0, 
  "fromAccountType": "string", 
  "fromEmail": "string", 
  "status": "string", 
  "toAccountType": "string", 
  "toEmail": "string", 
  "tranId": 0 
} 
 
UniversalTransferHistoryInfoVo
42.561. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
clientTranId
string
false
none
none
createTimeStamp
integer(int64)
false
none
none
fromAccountType
string
false
none
none
fromEmail
string
false
none
none
status
string
false
none
none
toAccountType
string
false
none
none
toEmail
string
false
none
none
tranId
integer(int64)
false
none
none
UniversalTransferResponse


---

## Page 299

sapi-v7.4.md
2024-05-08
299 / 419
{ 
  "clientTranId": "string", 
  "tranId": 0 
} 
 
UniversalTransferResponse
42.562. Properties
Name
Type
Required
Restrictions
Description
clientTranId
string
false
none
三⽅交易流⽔号
tranId
integer(int64)
false
none
事务操作id
UnsettleDetail
{ 
  "asset": "string", 
  "netReceive": 0 
} 
 
UnsettleDetail
42.563. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
netReceive
number
false
none
none
UnstakePreviewSapiDto
{ 
  "baseAmt": 0, 
  "baseAsset": "string", 
  "fee": 0, 
  "price": 0, 
  "quoteAmt": 0, 
  "quoteAsset": "string", 
  "slippage": 0 
} 
 
UnstakePreviewSapiDto
42.564. Properties
Name
Type
Required
Restrictions
Description
baseAmt
number
false
none
none
baseAsset
string
false
none
none
fee
number
false
none
none
price
number
false
none
none
quoteAmt
number
false
none
none
quoteAsset
string
false
none
none
slippage
number
false
none
none
UnwrapHistory
{ 
  "exchangeRate": "string", 
  "fromAmount": 0, 
  "fromAsset": "string", 


---

## Page 300

sapi-v7.4.md
2024-05-08
300 / 419
  "status": "string", 
  "time": 0, 
  "toAmount": 0, 
  "toAsset": "string" 
} 
 
UnwrapHistory
42.565. Properties
Name
Type
Required
Restrictions
Description
exchangeRate
string
false
none
none
fromAmount
number
false
none
none
fromAsset
string
false
none
none
status
string
false
none
none
time
integer(int64)
false
none
none
toAmount
number
false
none
none
toAsset
string
false
none
none
UnwrapHistoryResponse
{ 
  "rows": [ 
    { 
      "exchangeRate": "string", 
      "fromAmount": 0, 
      "fromAsset": "string", 
      "status": "string", 
      "time": 0, 
      "toAmount": 0, 
      "toAsset": "string" 
    } 
  ], 
  "total": 0 
} 
 
UnwrapHistoryResponse
42.566. Properties
Name
Type
Required
Restrictions
Description
rows
[UnwrapHistory]
false
none
none
total
integer(int64)
false
none
none
UnwrapResponse
{ 
  "success": true 
} 
 
UnwrapResponse
42.567. Properties
Name
Type
Required
Restrictions
Description
success
boolean
false
none
none
UpdateBrokerCommissionDeliveryResponse
{ 
  "makerAdjustment": 0, 


---

## Page 301

sapi-v7.4.md
2024-05-08
301 / 419
  "makerCommission": 0, 
  "pair": "string", 
  "subAccountId": 0, 
  "takerAdjustment": 0, 
  "takerCommission": 0 
} 
 
UpdateBrokerCommissionDeliveryResponse
42.568. Properties
Name
Type
Required
Restrictions
Description
makerAdjustment
integer(int32)
false
none
makerAdjustment
makerCommission
integer(int32)
false
none
makerCommission
pair
string
false
none
pair
subAccountId
integer(int64)
true
none
经销商⼦账户id
takerAdjustment
integer(int32)
false
none
takerAdjustment
takerCommission
integer(int32)
false
none
takerCommission
UserAdsCategoryResp
{ 
  "advClassifies": [ 
    "string" 
  ] 
} 
 
UserAdsCategoryResp
42.569. Properties
Name
Type
Required
Restrictions
Description
advClassifies
[string]
false
none
List of adv classify that can publish. mass
UserAsset
{ 
  "userId": 0, 
  "value": 0 
} 
 
UserAsset
42.570. Properties
Name
Type
Required
Restrictions
Description
userId
integer(int64)
false
none
none
value
number
false
none
none
UserAssetDividendResp
{ 
  "amount": 0, 
  "asset": "string", 
  "divTime": "2019-08-24T14:15:22Z", 
  "enInfo": "string", 
  "id": 0, 
  "tranId": 0 
} 
 


---

## Page 302

sapi-v7.4.md
2024-05-08
302 / 419
UserAssetDividendResp
42.571. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
divTime
string(date-time)
false
none
none
enInfo
string
false
none
none
id
integer(int64)
false
none
none
tranId
integer(int64)
false
none
none
UserAssetLogResp
{ 
  "asset": "string", 
  "delta": 0, 
  "time": "2019-08-24T14:15:22Z", 
  "type": 0 
} 
 
UserAssetLogResp
42.572. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
delta
number
false
none
none
time
string(date-time)
false
none
none
type
integer(int32)
false
none
none
UserAssetLogV2Resp
{ 
  "asset": "string", 
  "delta": 0, 
  "enInfo": "string", 
  "free": 0, 
  "freeze": 0, 
  "id": 0, 
  "info": "string", 
  "locked": 0, 
  "time": "2019-08-24T14:15:22Z", 
  "tranId": 0, 
  "type": 0, 
  "withdrawing": 0 
} 
 
UserAssetLogV2Resp
42.573. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
delta
number
false
none
none
enInfo
string
false
none
none
free
number
false
none
none
freeze
number
false
none
none
id
integer(int64)
false
none
none
info
string
false
none
none


---

## Page 303

sapi-v7.4.md
2024-05-08
303 / 419
Name
Type
Required
Restrictions
Description
locked
number
false
none
none
time
string(date-time)
false
none
none
tranId
integer(int64)
false
none
none
type
integer(int32)
false
none
none
withdrawing
number
false
none
none
UserAssetResp
{ 
  "asset": "string", 
  "free": 0, 
  "freeze": 0, 
  "locked": 0, 
  "updateId": 0, 
  "withdrawing": 0 
} 
 
UserAssetResp
42.574. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
free
number
false
none
none
freeze
number
false
none
none
locked
number
false
none
none
updateId
integer(int64)
false
none
none
withdrawing
number
false
none
none
UserAssetTransferBTCResp
{ 
  "details": [ 
    { 
      "amountFree": "string", 
      "asset": "string", 
      "assetFullName": "string", 
      "exchange": "string", 
      "toBNB": "string", 
      "toBNBOffExchange": "string", 
      "toBTC": "string" 
    } 
  ], 
  "dribbletPercentage": 0, 
  "totalTransferBNB": "string", 
  "totalTransferBtc": "string" 
} 
 
UserAssetTransferBTCResp
42.575. Properties
Name
Type
Required
Restrictions
Description
details
[UserDribbletAsset]
false
none
none
dribbletPercentage
number
false
none
none
totalTransferBNB
string
false
none
none
totalTransferBtc
string
false
none
none
UserAssetTransferBTCRespV2


---

## Page 304

sapi-v7.4.md
2024-05-08
304 / 419
{ 
  "details": [ 
    { 
      "amountFree": "string", 
      "asset": "string", 
      "assetFullName": "string", 
      "exchange": "string", 
      "toBNB": "string", 
      "toBNBOffExchange": "string", 
      "toBTC": "string" 
    } 
  ], 
  "dribbletPercentage": 0, 
  "totalTransferBtc": "string", 
  "totalTransferTargetAsset": "string" 
} 
 
UserAssetTransferBTCRespV2
42.576. Properties
Name
Type
Required
Restrictions
Description
details
[UserDribbletAsset]
false
none
none
dribbletPercentage
number
false
none
none
totalTransferBtc
string
false
none
none
totalTransferTargetAsset
string
false
none
none
UserDribbletAsset
{ 
  "amountFree": "string", 
  "asset": "string", 
  "assetFullName": "string", 
  "exchange": "string", 
  "toBNB": "string", 
  "toBNBOffExchange": "string", 
  "toBTC": "string" 
} 
 
UserDribbletAsset
42.577. Properties
Name
Type
Required
Restrictions
Description
amountFree
string
false
none
none
asset
string
false
none
none
assetFullName
string
false
none
none
exchange
string
false
none
none
toBNB
string
false
none
none
toBNBOffExchange
string
false
none
none
toBTC
string
false
none
none
UserGradeInstanceResp
{ 
  "agreementSigned": 0, 
  "emailStatus": 0, 
  "kycStatus": 0, 
  "marginStatus": 0, 
  "mobileStatus": 0, 
  "nickNameStatus": 0, 
  "userGrade": 0 
} 
 


---

## Page 305

sapi-v7.4.md
2024-05-08
305 / 419
UserGradeInstanceResp
42.578. Properties
Name
Type
Required
Restrictions
Description
agreementSigned
integer(int32)
false
none
If an agreement is signed. (1ÏYes, 0ÏNo)
emailStatus
integer(int32)
false
none
If email is set. (1ÏYes, 0ÏNo)
kycStatus
integer(int32)
false
none
If KYC is completed. (1ÏYes, 0ÏNo)
marginStatus
integer(int32)
false
none
If merchant has deposit amount. (1ÏYes, 0ÏNo)
mobileStatus
integer(int32)
false
none
If mobile number is bound. (1ÏYes, 0ÏNo)
nickNameStatus
integer(int32)
false
none
If the nickname is set (1ÏYes, 0ÏNo)
userGrade
integer(int32)
false
none
User grade (1: Normal user, 2: Verified User, 3: Verified Merchant)
UserGradeInstanceVo
{ 
  "agreementSigned": 0, 
  "authorityId": 0, 
  "createTime": "2019-08-24T14:15:22Z", 
  "emailStatus": 0, 
  "id": 0, 
  "kycStatus": 0, 
  "marginStatus": 0, 
  "mobileStatus": 0, 
  "nickNameStatus": 0, 
  "parentId": 0, 
  "qualificationId": 0, 
  "updateTime": "2019-08-24T14:15:22Z", 
  "userGradeQualificationVo": { 
    "accountGrade": 0, 
    "accountType": 0, 
    "agreement": 0, 
    "countryCode": "string", 
    "createTime": "2019-08-24T14:15:22Z", 
    "defaultAuthority": 0, 
    "email": 0, 
    "gradeName": "string", 
    "id": 0, 
    "kycVerify": 0, 
    "margin": 0, 
    "mobile": 0, 
    "nickName": 0, 
    "typeName": "string", 
    "updateTime": "2019-08-24T14:15:22Z" 
  }, 
  "userId": 0 
} 
 
UserGradeInstanceVo
42.579. Properties
Name
Type
Required
Restrictions
Description
agreementSigned
integer(int32)
false
none
none
authorityId
integer(int64)
false
none
none
createTime
string(date-time)
false
none
none
emailStatus
integer(int32)
false
none
none
id
integer(int64)
false
none
none
kycStatus
integer(int32)
false
none
none
marginStatus
integer(int32)
false
none
none
mobileStatus
integer(int32)
false
none
none
nickNameStatus
integer(int32)
false
none
none


---

## Page 306

sapi-v7.4.md
2024-05-08
306 / 419
Name
Type
Required
Restrictions
Description
parentId
integer(int64)
false
none
none
qualificationId
integer(int64)
false
none
none
updateTime
string(date-time)
false
none
none
userGradeQualificationVo
UserGradeQualificationVo
false
none
none
userId
integer(int64)
false
none
none
UserGradeQualificationVo
{ 
  "accountGrade": 0, 
  "accountType": 0, 
  "agreement": 0, 
  "countryCode": "string", 
  "createTime": "2019-08-24T14:15:22Z", 
  "defaultAuthority": 0, 
  "email": 0, 
  "gradeName": "string", 
  "id": 0, 
  "kycVerify": 0, 
  "margin": 0, 
  "mobile": 0, 
  "nickName": 0, 
  "typeName": "string", 
  "updateTime": "2019-08-24T14:15:22Z" 
} 
 
UserGradeQualificationVo
42.580. Properties
Name
Type
Required
Restrictions
Description
accountGrade
integer(int32)
false
none
none
accountType
integer(int32)
false
none
none
agreement
integer(int32)
false
none
none
countryCode
string
false
none
none
createTime
string(date-time)
false
none
none
defaultAuthority
integer(int64)
false
none
none
email
integer(int32)
false
none
none
gradeName
string
false
none
none
id
integer(int64)
false
none
none
kycVerify
integer(int32)
false
none
none
margin
integer(int32)
false
none
none
mobile
integer(int32)
false
none
none
nickName
integer(int32)
false
none
none
typeName
string
false
none
none
updateTime
string(date-time)
false
none
none
UserInterestHistoryUnionDisplayResp
{ 
  "asset": "string", 
  "interest": 0, 
  "lendingType": "CUSTOMIZED_FIXED", 
  "productName": "string", 
  "time": 0 
} 
 


---

## Page 307

sapi-v7.4.md
2024-05-08
307 / 419
UserInterestHistoryUnionDisplayResp
42.581. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
币种
interest
number
false
none
利息⾦额
lendingType
string
false
none
类型：活期或者定期
productName
string
false
none
产品名称
time
integer(int64)
false
none
收⼊时间
42.581.1. Enumerated Values
Property
Value
lendingType
CUSTOMIZED_FIXED
lendingType
DAILY
lendingType
EXPERIENCE_COUPON
lendingType
REGULAR
lendingType
SUPER_MINING
UserKycResp
{ 
  "addressStatus": "string", 
  "kycType": "string" 
} 
 
UserKycResp
42.582. Properties
Name
Type
Required
Restrictions
Description
addressStatus
string
false
none
Address verification status (PROCESS, PASS, REFUSED, REVIEW, SKIP, FORBID_PASS: Forbidden (non-
compliant nationality passed))
kycType
string
false
none
KYC verification type. (1: Individual, 2: Cooperate, -1: Not verified)
UserKycVo
{ 
  "address": "string", 
  "addressStatus": "string", 
  "basicStatus": "string", 
  "certificateStatus": 0, 
  "companyName": "string", 
  "countyCode": "string", 
  "createTime": "2019-08-24T14:15:22Z", 
  "faceStatus": "string", 
  "firstName": "string", 
  "idNo": "string", 
  "identityStatus": "string", 
  "kycLevel": 0, 
  "kycStatus": "string", 
  "kycType": "string", 
  "lastName": "string", 
  "middleName": "string", 
  "updateTime": "2019-08-24T14:15:22Z", 
  "userId": 0 
} 
 
UserKycVo
42.583. Properties


---

## Page 308

sapi-v7.4.md
2024-05-08
308 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
address
string
false
none
none
addressStatus
string
false
none
none
basicStatus
string
false
none
none
certificateStatus
integer(int32)
false
none
none
companyName
string
false
none
none
countyCode
string
false
none
none
createTime
string(date-time)
false
none
none
faceStatus
string
false
none
none
firstName
string
false
none
none
idNo
string
false
none
none
identityStatus
string
false
none
none
kycLevel
integer(int32)
false
none
none
kycStatus
string
false
none
none
kycType
string
false
none
none
lastName
string
false
none
none
middleName
string
false
none
none
updateTime
string(date-time)
false
none
none
userId
integer(int64)
false
none
none
UserLiabilityResponse
{ 
  "amount": 0, 
  "asset": "string" 
} 
 
UserLiabilityResponse
42.584. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
asset
string
false
none
none
UserMicroassets
{ 
  "clientId": "string", 
  "operateTime": "2019-08-24T14:15:22Z", 
  "totalServiceChargeAmount": 0, 
  "totalTransferedAmount": 0, 
  "transId": 0, 
  "userAssetDribbletDetails": [ 
    { 
      "amount": 0, 
      "fromAsset": "string", 
      "operateTime": "2019-08-24T14:15:22Z", 
      "serviceChargeAmount": 0, 
      "transId": 0, 
      "transferedAmount": 0, 
      "uid": "string" 
    } 
  ] 
} 
 
UserMicroassets


---

## Page 309

sapi-v7.4.md
2024-05-08
309 / 419
42.585. Properties
Name
Type
Required
Restrictions
Description
clientId
string
false
none
none
operateTime
string(date-time)
false
none
none
totalServiceChargeAmount
number
false
none
none
totalTransferedAmount
number
false
none
none
transId
integer(int64)
false
none
none
userAssetDribbletDetails
[UserMicroassetsDetail]
false
none
none
UserMicroassetsDetail
{ 
  "amount": 0, 
  "fromAsset": "string", 
  "operateTime": "2019-08-24T14:15:22Z", 
  "serviceChargeAmount": 0, 
  "transId": 0, 
  "transferedAmount": 0, 
  "uid": "string" 
} 
 
UserMicroassetsDetail
42.586. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
fromAsset
string
false
none
none
operateTime
string(date-time)
false
none
none
serviceChargeAmount
number
false
none
none
transId
integer(int64)
false
none
none
transferedAmount
number
false
none
none
uid
string
false
none
none
UserOrderHistoryStatsResp
{ 
  "completedOrderNum": 0, 
  "completedOrderNumOfLatest30day": 0, 
  "finishRate": 0, 
  "finishRateLatest30Day": 0, 
  "numberOfTradesWithCounterpartyCompleted30day": 0, 
  "registerDays": 0 
} 
 
UserOrderHistoryStatsResp
42.587. Properties
Name
Type
Required
Restrictions
Description
completedOrderNum
integer(int64)
false
none
历史所有订单完成数
completedOrderNumOfLatest30day
integer(int64)
false
none
30⽇所有订单完成数
finishRate
number(double)
false
none
历史完成率
finishRateLatest30Day
number(double)
false
none
30⽇完成率
numberOfTradesWithCounterpartyCompleted30day
integer(int32)
false
none
number of trades with counterparty completed last 30
days
registerDays
integer(int32)
false
none
account register days


---

## Page 310

sapi-v7.4.md
2024-05-08
310 / 419
UserOrderHistoryStatsVo
{ 
  "accountAge": 0, 
  "appealedOrderCountHistorical": 0, 
  "appealedOrderCountLast30Days": 0, 
  "appealedRateHistorical": 0, 
  "appealedRateLast30Days": 0, 
  "avgPayTime": 0, 
  "avgPayTimeOfLatest30day": 0, 
  "avgReleaseTime": 0, 
  "avgReleaseTimeOfLatest30day": 0, 
  "buyOrderNum": 0, 
  "buyOrderNumOfLatest30day": 0, 
  "canceledBuyOrderNum": 0, 
  "canceledBuyOrderNumOfLatest30day": 0, 
  "completedBuyOrderNum": 0, 
  "completedBuyOrderNumOfLatest30day": 0, 
  "completedBuyOrderTotalBtcAmount": 0, 
  "completedBuyOrderTotalBtcAmountOfLatest30day": 0, 
  "completedOrderNum": 0, 
  "completedOrderNumOfLatest30day": 0, 
  "completedOrderTotalBtcAmount": 0, 
  "completedOrderTotalBtcAmountOfLatest30day": 0, 
  "completedSellOrderNum": 0, 
  "completedSellOrderNumOfLatest30day": 0, 
  "completedSellOrderTotalBtcAmount": 0, 
  "completedSellOrderTotalBtcAmountOfLatest30day": 0, 
  "counterpartyNum": 0, 
  "creditScore": 0, 
  "finishRate": 0, 
  "finishRateLatest30Day": 0 
} 
 
UserOrderHistoryStatsVo
42.588. Properties
Name
Type
Required
Restrictions
Description
accountAge
integer(int32)
false
none
Account age in day
appealedOrderCountHistorical
integer(int64)
false
none
No of orders appealed since registration
appealedOrderCountLast30Days
integer(int64)
false
none
No of orders appealed in the last 30 days
appealedRateHistorical
number
false
none
Appeal rate since registration
appealedRateLast30Days
number
false
none
Appeal rate in the last 30 days
avgPayTime
number(double)
false
none
历史平均付款时间
avgPayTimeOfLatest30day
number(double)
false
none
30⽇平均付款时间
avgReleaseTime
number(double)
false
none
历史平均放⾏时间
avgReleaseTimeOfLatest30day
number(double)
false
none
30⽇平均放⾏时间
buyOrderNum
integer(int64)
false
none
历史作为买⽅所有订单数
buyOrderNumOfLatest30day
integer(int64)
false
none
30⽇作为买⽅所有订单数
canceledBuyOrderNum
integer(int64)
false
none
历史作为买⽅订单取消数
canceledBuyOrderNumOfLatest30day
integer(int64)
false
none
30⽇作为买⽅订单取消数
completedBuyOrderNum
integer(int64)
false
none
历史购买订单完成数
completedBuyOrderNumOfLatest30day
integer(int64)
false
none
30⽇购买订单完成数
completedBuyOrderTotalBtcAmount
number
false
none
历史完成购买订单BTC交易额
completedBuyOrderTotalBtcAmountOfLatest30day
number
false
none
30⽇完成购买订单BTC交易额
completedOrderNum
integer(int64)
false
none
历史所有订单完成数
completedOrderNumOfLatest30day
integer(int64)
false
none
30⽇所有订单完成数
completedOrderTotalBtcAmount
number
false
none
历史完成订单BTC交易额
completedOrderTotalBtcAmountOfLatest30day
number
false
none
30⽇完成订单BTC交易额


---

## Page 311

sapi-v7.4.md
2024-05-08
311 / 419
Name
Type
Required
Restrictions
Description
completedSellOrderNum
integer(int64)
false
none
历史出售订单完成数
completedSellOrderNumOfLatest30day
integer(int64)
false
none
30⽇出售订单完成数
completedSellOrderTotalBtcAmount
number
false
none
历史完成出售订单BTC交易额
completedSellOrderTotalBtcAmountOfLatest30day
number
false
none
30⽇完成出售订单BTC交易额
counterpartyNum
integer(int32)
false
none
交易过的对⽅的⽤户数量
creditScore
number(double)
false
none
⽤户信⽤分 实时数据
finishRate
number(double)
false
none
历史完成率
finishRateLatest30Day
number(double)
false
none
30⽇完成率
UserOrderListReq
{ 
  "advNo": "string", 
  "asset": "string", 
  "endDate": 0, 
  "order": "string", 
  "orderStatus": 0, 
  "orderStatusList": [ 
    0 
  ], 
  "page": 0, 
  "payType": 0, 
  "rows": 0, 
  "sort": "string", 
  "startDate": 0, 
  "tradeType": "string" 
} 
 
UserOrderListReq
42.589. Properties
Name
Type
Required
Restrictions
Description
advNo
string
false
none
Adv number
asset
string
false
none
Crypto asset: BTC
endDate
integer(int64)
false
none
Query rage end date
order
string
false
none
Page order by
orderStatus
integer(int32)
false
none
Order status (1: Wait for payment, 2: Wait for release, 3: Appealing, 4: Completed, 6: Cancelled,
7: Cancelled by system
orderStatusList
[integer]
false
none
Order status (1: Wait for payment, 2: Wait for release, 3: Appealing, 4: Completed, 6: Cancelled,
7: Cancelled by system
page
integer(int32)
true
none
Page number to query. Start = 1
payType
integer(int32)
false
none
Payment method, e.g.: BANK, WECHAT
rows
integer(int32)
true
none
Rows to query per page. Suggested = 20
sort
string
false
none
Page sorting by (asc, desc)
startDate
integer(int64)
false
none
Query range start date
tradeType
string
false
none
Order trade type. 0: BUY, 1: SELL
UserStatsResp
{ 
  "avgPayTimeOfLatest30day": 0, 
  "avgReleaseTimeOfLatest30day": 0, 
  "completedBuyOrderNum": 0, 
  "completedBuyOrderNumOfLatest30day": 0, 
  "completedBuyOrderTotalBtcAmount": 0, 
  "completedOrderNum": 0, 
  "completedOrderNumOfLatest30day": 0, 
  "completedOrderTotalBtcAmount": 0, 


---

## Page 312

sapi-v7.4.md
2024-05-08
312 / 419
  "completedOrderTotalBtcAmountOfLatest30day": 0, 
  "completedSellOrderNum": 0, 
  "completedSellOrderNumOfLatest30day": 0, 
  "completedSellOrderTotalBtcAmount": 0, 
  "finishRateLatest30day": 0, 
  "firstOrderDays": 0, 
  "payMethodCount": 0, 
  "registerDays": 0 
} 
 
UserStatsResp
42.590. Properties
Name
Type
Required
Restrictions
Description
avgPayTimeOfLatest30day
number(double)
false
none
30-day average payment time
avgReleaseTimeOfLatest30day
number(double)
false
none
30-day average release time
completedBuyOrderNum
integer(int64)
false
none
Total number of completed historical buy orders
completedBuyOrderNumOfLatest30day
integer(int64)
false
none
Number of completed buy orders in the last 30 days
completedBuyOrderTotalBtcAmount
number
false
none
Total BTC transaction amount of completed historical buy
orders
completedOrderNum
integer(int64)
false
none
Total number of completed historical orders
completedOrderNumOfLatest30day
integer(int64)
false
none
Number of completed orders in the last 30 days
completedOrderTotalBtcAmount
number
false
none
Total BTC transaction amount of completed historical orders
completedOrderTotalBtcAmountOfLatest30day
number
false
none
Total BTC transaction amount of completed orders in the last
30 days
completedSellOrderNum
integer(int64)
false
none
Total number of completed historical sell orders
completedSellOrderNumOfLatest30day
integer(int64)
false
none
Number of completed sell orders in the last 30 days
completedSellOrderTotalBtcAmount
number
false
none
Total BTC transaction amount of completed historical sell
orders
finishRateLatest30day
number(double)
false
none
30-day completion rate
firstOrderDays
integer(int32)
false
none
User first order days
payMethodCount
integer(int32)
false
none
Number of payment methods
registerDays
integer(int32)
false
none
User registration day
UserTotalAssetModel
{ 
  "card": 0, 
  "delivery": 0, 
  "future": 0, 
  "inValid": true, 
  "isolatedMargin": 0, 
  "main": 0, 
  "margin": 0, 
  "saving": 0, 
  "time": "2019-08-24T14:15:22Z", 
  "timestamp": 0, 
  "toption": 0, 
  "total": 0 
} 
 
UserTotalAssetModel
42.591. Properties
Name
Type
Required
Restrictions
Description
card
number
false
none
card
delivery
number
false
none
delivery
future
number
false
none
future


---

## Page 313

sapi-v7.4.md
2024-05-08
313 / 419
Name
Type
Required
Restrictions
Description
inValid
boolean
false
none
none
isolatedMargin
number
false
none
isolatedMargin
main
number
false
none
main
margin
number
false
none
margin
saving
number
false
none
saving
time
string(date-time)
false
none
时间
timestamp
integer(int64)
false
none
时间戳
toption
number
false
none
toption
total
number
false
none
total
UserTotalAssetResponse
{ 
  "endDay": "2019-08-24", 
  "md5Uid": "string", 
  "quoteAsset": "string", 
  "startDay": "2019-08-24", 
  "userId": 0, 
  "userTotalAssetModels": [ 
    { 
      "card": 0, 
      "delivery": 0, 
      "future": 0, 
      "inValid": true, 
      "isolatedMargin": 0, 
      "main": 0, 
      "margin": 0, 
      "saving": 0, 
      "time": "2019-08-24T14:15:22Z", 
      "timestamp": 0, 
      "toption": 0, 
      "total": 0 
    } 
  ] 
} 
 
UserTotalAssetResponse
42.592. Properties
Name
Type
Required
Restrictions
Description
endDay
string(date)
false
none
结束⽇期
md5Uid
string
false
none
性能测试⽤
quoteAsset
string
false
none
quote token
startDay
string(date)
false
none
起始⽇期
userId
integer(int64)
false
none
⽤户主账户ID
userTotalAssetModels
[UserTotalAssetModel]
false
none
none
UserTotalAssetSummary
{ 
  "email": "string", 
  "status": 0, 
  "subUserId": 0, 
  "totalAssetOfBtc": 0, 
  "totalLiabilityOfBtc": 0, 
  "totalNetAssetOfBtc": 0 
} 
 
UserTotalAssetSummary


---

## Page 314

sapi-v7.4.md
2024-05-08
314 / 419
42.593. Properties
Name
Type
Required
Restrictions
Description
email
string
false
none
⼦账户邮箱
status
integer(int64)
false
none
⼦账户是否启⽤
subUserId
integer(int64)
false
none
⼦账户id
totalAssetOfBtc
number
false
none
⼦账户总资产(单位: BTC)
totalLiabilityOfBtc
number
false
none
⼦账户总负债(单位: BTC)
totalNetAssetOfBtc
number
false
none
⼦账户净资产(单位: BTC)
UserVo
{ 
  "advConfirmTime": 0, 
  "badges": [ 
    "string" 
  ], 
  "businessMobile": "string", 
  "businessStatus": 0, 
  "complaintCount": 0, 
  "countyCode": "string", 
  "createTime": "2019-08-24T14:15:22Z", 
  "email": "string", 
  "eqMargin": 0, 
  "eqMarginUnit": "string", 
  "fiatTradingAccount": 0, 
  "firstOrderDays": 0, 
  "fundpwdStatus": 0, 
  "id": 0, 
  "informMethods": "string", 
  "maliceInitiatorCount": 0, 
  "margin": 0, 
  "marginAsset": { 
    "asset": "string", 
    "createTime": "2019-08-24T14:15:22Z", 
    "decimalScale": 0, 
    "iconUrl": "string", 
    "isEnable": 0, 
    "isTransVisible": 0, 
    "name": "string", 
    "ranking": 0, 
    "updateTime": "2019-08-24T14:15:22Z" 
  }, 
  "marginFreeze": 0, 
  "marginStatsItems": [ 
    { 
      "margin": 0, 
      "marginUnit": "string" 
    } 
  ], 
  "marginUnit": "string", 
  "maskedBusinessMobile": "string", 
  "maskedEmail": "string", 
  "merchantType": "string", 
  "mobile": "string", 
  "mobileDisplayStatus": 0, 
  "monthFinishRate": 0, 
  "monthOrderCount": 0, 
  "nickColor": "string", 
  "nickName": "string", 
  "onlineStatus": 0, 
  "orderCount": 0, 
  "overComplained": 0, 
  "parentId": 0, 
  "payMethodCount": 0, 
  "proMerchantVo": { 
    "merchantDescription": "string", 
    "merchantLogo": "string" 
  }, 
  "realName": "string", 
  "registerDays": 0, 
  "registrationTime": "2019-08-24T14:15:22Z", 
  "tradingAccount": 0, 
  "updateTime": "2019-08-24T14:15:22Z", 


---

## Page 315

sapi-v7.4.md
2024-05-08
315 / 419
  "userGradeInstanceVo": { 
    "agreementSigned": 0, 
    "authorityId": 0, 
    "createTime": "2019-08-24T14:15:22Z", 
    "emailStatus": 0, 
    "id": 0, 
    "kycStatus": 0, 
    "marginStatus": 0, 
    "mobileStatus": 0, 
    "nickNameStatus": 0, 
    "parentId": 0, 
    "qualificationId": 0, 
    "updateTime": "2019-08-24T14:15:22Z", 
    "userGradeQualificationVo": { 
      "accountGrade": 0, 
      "accountType": 0, 
      "agreement": 0, 
      "countryCode": "string", 
      "createTime": "2019-08-24T14:15:22Z", 
      "defaultAuthority": 0, 
      "email": 0, 
      "gradeName": "string", 
      "id": 0, 
      "kycVerify": 0, 
      "margin": 0, 
      "mobile": 0, 
      "nickName": 0, 
      "typeName": "string", 
      "updateTime": "2019-08-24T14:15:22Z" 
    }, 
    "userId": 0 
  }, 
  "userId": 0, 
  "userKycVo": { 
    "address": "string", 
    "addressStatus": "string", 
    "basicStatus": "string", 
    "certificateStatus": 0, 
    "companyName": "string", 
    "countyCode": "string", 
    "createTime": "2019-08-24T14:15:22Z", 
    "faceStatus": "string", 
    "firstName": "string", 
    "idNo": "string", 
    "identityStatus": "string", 
    "kycLevel": 0, 
    "kycStatus": "string", 
    "kycType": "string", 
    "lastName": "string", 
    "middleName": "string", 
    "updateTime": "2019-08-24T14:15:22Z", 
    "userId": 0 
  }, 
  "userNo": "string", 
  "userOrderHistoryStatsVo": { 
    "accountAge": 0, 
    "appealedOrderCountHistorical": 0, 
    "appealedOrderCountLast30Days": 0, 
    "appealedRateHistorical": 0, 
    "appealedRateLast30Days": 0, 
    "avgPayTime": 0, 
    "avgPayTimeOfLatest30day": 0, 
    "avgReleaseTime": 0, 
    "avgReleaseTimeOfLatest30day": 0, 
    "buyOrderNum": 0, 
    "buyOrderNumOfLatest30day": 0, 
    "canceledBuyOrderNum": 0, 
    "canceledBuyOrderNumOfLatest30day": 0, 
    "completedBuyOrderNum": 0, 
    "completedBuyOrderNumOfLatest30day": 0, 
    "completedBuyOrderTotalBtcAmount": 0, 
    "completedBuyOrderTotalBtcAmountOfLatest30day": 0, 
    "completedOrderNum": 0, 
    "completedOrderNumOfLatest30day": 0, 
    "completedOrderTotalBtcAmount": 0, 
    "completedOrderTotalBtcAmountOfLatest30day": 0, 
    "completedSellOrderNum": 0, 
    "completedSellOrderNumOfLatest30day": 0, 
    "completedSellOrderTotalBtcAmount": 0, 
    "completedSellOrderTotalBtcAmountOfLatest30day": 0, 
    "counterpartyNum": 0, 


---

## Page 316

sapi-v7.4.md
2024-05-08
316 / 419
    "creditScore": 0, 
    "finishRate": 0, 
    "finishRateLatest30Day": 0 
  }, 
  "userOrderInProgressStatsVo": { 
    "buyerPayedCount": 0, 
    "inAppealCount": 0, 
    "inAppealCountAfterBuyerPaid": 0, 
    "inAppealCountAfterCancelled": 0, 
    "inAppealCountAfterCancelledBySystem": 0, 
    "inAppealCountAfterCompleted": 0, 
    "inProcessCount": 0, 
    "tradingCount": 0, 
    "userId": 0 
  }, 
  "userType": "string" 
} 
 
UserVo
42.594. Properties
Name
Type
Required
Restrictions
Description
advConfirmTime
integer(int32)
false
none
none
badges
[string]
false
none
merchant's badges
businessMobile
string
false
none
none
businessStatus
integer(int32)
false
none
none
complaintCount
integer(int32)
false
none
none
countyCode
string
false
none
none
createTime
string(date-time)
false
none
none
email
string
false
none
none
eqMargin
number
false
none
Equivalent Margin
eqMarginUnit
string
false
none
Equivalent Margin Symbol e.g. USDT, BNB
fiatTradingAccount
integer(int64)
false
none
none
firstOrderDays
integer(int32)
false
none
none
fundpwdStatus
integer(int32)
false
none
none
id
integer(int64)
false
none
none
informMethods
string
false
none
none
maliceInitiatorCount
integer(int32)
false
none
none
margin
number
false
none
none
marginAsset
DigitalCurrencyVo
false
none
none
marginFreeze
number
false
none
none
marginStatsItems
[Margin_Statistic_Item]
false
none
Margin statistic
marginUnit
string
false
none
none
maskedBusinessMobile
string
false
none
none
maskedEmail
string
false
none
none
merchantType
string
false
none
商户类型：MASS_MERCHANT 普通商户，BLOCK_MERCHANT ⼤宗商
户
mobile
string
false
none
none
mobileDisplayStatus
integer(int32)
false
none
none
monthFinishRate
number
false
none
none
monthOrderCount
integer(int32)
false
none
none
nickColor
string
false
none
none
nickName
string
false
none
none
onlineStatus
integer(int32)
false
none
none


---

## Page 317

sapi-v7.4.md
2024-05-08
317 / 419
Name
Type
Required
Restrictions
Description
orderCount
integer(int32)
false
none
none
overComplained
integer(int32)
false
none
none
parentId
integer(int64)
false
none
none
payMethodCount
integer(int32)
false
none
none
proMerchantVo
ProMerchantVo
false
none
brand merchant
realName
string
false
none
none
registerDays
integer(int32)
false
none
none
registrationTime
string(date-time)
false
none
none
tradingAccount
integer(int64)
false
none
none
updateTime
string(date-time)
false
none
none
userGradeInstanceVo
UserGradeInstanceVo
false
none
none
userId
integer(int64)
false
none
none
userKycVo
UserKycVo
false
none
none
userNo
string
false
none
none
userOrderHistoryStatsVo
UserOrderHistoryStatsVo
false
none
none
userOrderInProgressStatsVo
_6
false
none
none
userType
string
false
none
none
VipCollateralAssetsDataForSapiResp
{ 
  "_1stCollateralRange": "string", 
  "_1stCollateralRatio": "string", 
  "_2ndCollateralRange": "string", 
  "_2ndCollateralRatio": "string", 
  "_3rdCollateralRange": "string", 
  "_3rdCollateralRatio": "string", 
  "_4thCollateralRange": "string", 
  "_4thCollateralRatio": "string", 
  "_5thCollateralRange": "string", 
  "_5thCollateralRatio": "string", 
  "_6thCollateralRange": "string", 
  "_6thCollateralRatio": "string", 
  "_7thCollateralRange": "string", 
  "_7thCollateralRatio": "string", 
  "_8thCollateralRange": "string", 
  "_8thCollateralRatio": "string", 
  "_9thCollateralRange": "string", 
  "_9thCollateralRatio": "string", 
  "collateralCoin": "string" 
} 
 
VipCollateralAssetsDataForSapiResp
42.595. Properties
Name
Type
Required
Restrictions
Description
_1stCollateralRange
string
false
none
none
_1stCollateralRatio
string
false
none
none
_2ndCollateralRange
string
false
none
none
_2ndCollateralRatio
string
false
none
none
_3rdCollateralRange
string
false
none
none
_3rdCollateralRatio
string
false
none
none
_4thCollateralRange
string
false
none
none
_4thCollateralRatio
string
false
none
none
_5thCollateralRange
string
false
none
none


---

## Page 318

sapi-v7.4.md
2024-05-08
318 / 419
Name
Type
Required
Restrictions
Description
_5thCollateralRatio
string
false
none
none
_6thCollateralRange
string
false
none
none
_6thCollateralRatio
string
false
none
none
_7thCollateralRange
string
false
none
none
_7thCollateralRatio
string
false
none
none
_8thCollateralRange
string
false
none
none
_8thCollateralRatio
string
false
none
none
_9thCollateralRange
string
false
none
none
_9thCollateralRatio
string
false
none
none
collateralCoin
string
false
none
none
VipIntRateHistoryResponse
{ 
  "asset": "string", 
  "dailyInterestRate": 0, 
  "timestamp": 0, 
  "vipLevel": 0 
} 
 
VipIntRateHistoryResponse
42.596. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
币种名称
dailyInterestRate
number
false
none
利率
timestamp
integer(int64)
false
none
时间
vipLevel
integer(int32)
false
none
VIP等级
VipLatestFlexRateForVipForSapiResp
{ 
  "asset": "string", 
  "flexibleDailyInterestRate": 0, 
  "flexibleHourlyInterestRate": 0, 
  "flexibleYearlyInterestRate": 0, 
  "time": 0 
} 
 
VipLatestFlexRateForVipForSapiResp
42.597. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
flexibleDailyInterestRate
number
false
none
none
flexibleHourlyInterestRate
number
false
none
none
flexibleYearlyInterestRate
number
false
none
none
time
integer(int64)
false
none
none
VipLoanableAssetsDataForSapiResp
{ 
  "_30dDailyInterestRate": 0, 
  "_30dYearlyInterestRate": 0, 


---

## Page 319

sapi-v7.4.md
2024-05-08
319 / 419
  "_60dDailyInterestRate": 0, 
  "_60dYearlyInterestRate": 0, 
  "_flexibleDailyInterestRate": 0, 
  "_flexibleHourlyInterestRate": 0, 
  "_flexibleYearlyInterestRate": 0, 
  "loanCoin": "string", 
  "maxLimit": 0, 
  "minLimit": 0, 
  "vipLevel": 0 
} 
 
VipLoanableAssetsDataForSapiResp
42.598. Properties
Name
Type
Required
Restrictions
Description
_30dDailyInterestRate
number
false
none
none
_30dYearlyInterestRate
number
false
none
none
_60dDailyInterestRate
number
false
none
none
_60dYearlyInterestRate
number
false
none
none
_flexibleDailyInterestRate
number
false
none
none
_flexibleHourlyInterestRate
number
false
none
none
_flexibleYearlyInterestRate
number
false
none
none
loanCoin
string
false
none
none
maxLimit
number
false
none
none
minLimit
number
false
none
none
vipLevel
integer(int32)
false
none
none
WalletBalanceResp
{ 
  "activate": true, 
  "balance": 0, 
  "walletName": "string" 
} 
 
WalletBalanceResp
42.599. Properties
Name
Type
Required
Restrictions
Description
activate
boolean
false
none
是否已激活
balance
number
false
none
账户余额
walletName
string
false
none
钱包的多语⾔⽂案
WalletTransferCloudResp
{ 
  "fromErrorCode": "string", 
  "fromResponse": "string", 
  "fromStatus": "FAILURE", 
  "toErrorCode": "string", 
  "toResponse": "string", 
  "toStatus": "FAILURE", 
  "tranId": 0 
} 
 
WalletTransferCloudResp
42.600. Properties


---

## Page 320

sapi-v7.4.md
2024-05-08
320 / 419
Name
Type
Required
Restrictions
Description
fromErrorCode
string
false
none
转出失败错误码
fromResponse
string
false
none
转出mbx返回信息，仅供调⽤⽅参考，⽅便排查问题
fromStatus
string
false
none
转出状态
toErrorCode
string
false
none
转⼊失败错误码
toResponse
string
false
none
转⼊mbx返回信息，仅供调⽤⽅参考，⽅便排查问题
toStatus
string
false
none
转⼊状态
tranId
integer(int64)
false
none
划转id
42.600.1. Enumerated Values
Property
Value
fromStatus
FAILURE
fromStatus
INIT
fromStatus
PROCESS
fromStatus
SUCCESS
toStatus
FAILURE
toStatus
INIT
toStatus
PROCESS
toStatus
SUCCESS
WalletTransferHistoryResp
{ 
  "amount": 0, 
  "asset": "string", 
  "status": "CONFIRMED", 
  "timestamp": 0, 
  "tranId": 0, 
  "type": "CMFUTURE_FUNDING" 
} 
 
WalletTransferHistoryResp
42.601. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
划转⾦额
asset
string
false
none
资产名称
status
string
false
none
状态
timestamp
integer(int64)
false
none
划转时间
tranId
integer(int64)
false
none
划转ID
type
string
false
none
划转类型
42.601.1. Enumerated Values
Property
Value
status
CONFIRMED
status
FAILED
status
PENDING
type
CMFUTURE_FUNDING
type
CMFUTURE_MAIN
type
CMFUTURE_MARGIN
type
FUNDING_CMFUTURE


---

## Page 321

sapi-v7.4.md
2024-05-08
321 / 419
Property
Value
type
FUNDING_MAIN
type
FUNDING_MARGIN
type
FUNDING_OPTION
type
FUNDING_UMFUTURE
type
ISOLATEDMARGIN_ISOLATEDMARGIN
type
ISOLATEDMARGIN_MARGIN
type
ISOLATED_MARGIN_MAIN
type
MAIN_CMFUTURE
type
MAIN_FUNDING
type
MAIN_ISOLATED_MARGIN
type
MAIN_MARGIN
type
MAIN_MINING
type
MAIN_OPTION
type
MAIN_PORTFOLIO_MARGIN
type
MAIN_UMFUTURE
type
MARGIN_CMFUTURE
type
MARGIN_FUNDING
type
MARGIN_ISOLATEDMARGIN
type
MARGIN_MAIN
type
MARGIN_MINING
type
MARGIN_OPTION
type
MARGIN_UMFUTURE
type
MINING_MAIN
type
MINING_MARGIN
type
MINING_UMFUTURE
type
OPTION_FUNDING
type
OPTION_MAIN
type
OPTION_MARGIN
type
OPTION_UMFUTURE
type
PORTFOLIO_MARGIN_MAIN
type
UMFUTURE_FUNDING
type
UMFUTURE_MAIN
type
UMFUTURE_MARGIN
type
UMFUTURE_OPTION
WalletTransferResp
{ 
  "tranId": 0 
} 
 
WalletTransferResp
42.602. Properties
Name
Type
Required
Restrictions
Description
tranId
integer(int64)
false
none
none
WbethRewardsDetail


---

## Page 322

sapi-v7.4.md
2024-05-08
322 / 419
{ 
  "amountInETH": 0, 
  "annualPercentageRate": 0, 
  "holding": 0, 
  "holdingInETH": 0, 
  "time": 0 
} 
 
WbethRewardsDetail
42.603. Properties
Name
Type
Required
Restrictions
Description
amountInETH
number
false
none
none
annualPercentageRate
number
false
none
none
holding
number
false
none
none
holdingInETH
number
false
none
none
time
integer(int64)
false
none
none
WbethRewardsHistoryResponse
{ 
  "estRewardsInETH": 0, 
  "rows": [ 
    { 
      "amountInETH": 0, 
      "annualPercentageRate": 0, 
      "holding": 0, 
      "holdingInETH": 0, 
      "time": 0 
    } 
  ], 
  "total": 0 
} 
 
WbethRewardsHistoryResponse
42.604. Properties
Name
Type
Required
Restrictions
Description
estRewardsInETH
number
false
none
none
rows
[WbethRewardsDetail]
false
none
none
total
integer(int64)
false
none
none
WithdrawAddressResp
{ 
  "address": "string", 
  "addressTag": "string", 
  "coin": "string", 
  "name": "string", 
  "network": "string", 
  "origin": "string", 
  "originType": "string", 
  "whiteStatus": true 
} 
 
WithdrawAddressResp
42.605. Properties
Name
Type
Required
Restrictions
Description


---

## Page 323

sapi-v7.4.md
2024-05-08
323 / 419
Name
Type
Required
Restrictions
Description
address
string
false
none
none
addressTag
string
false
none
none
coin
string
false
none
none
name
string
false
none
none
network
string
false
none
none
origin
string
false
none
none
originType
string
false
none
none
whiteStatus
boolean
false
none
none
WithdrawHistoryResp
{ 
  "address": "string", 
  "addressTag": "string", 
  "amount": 0, 
  "applyTime": "string", 
  "coin": "string", 
  "completeTime": "string", 
  "confirmNo": 0, 
  "extensionInfo": "string", 
  "id": "string", 
  "info": "string", 
  "network": "string", 
  "status": 0, 
  "transactionFee": 0, 
  "transferType": 0, 
  "txId": "string", 
  "txKey": "string", 
  "walletType": 0, 
  "withdrawOrderId": "string" 
} 
 
WithdrawHistoryResp
42.606. Properties
Name
Type
Required
Restrictions
Description
address
string
false
none
none
addressTag
string
false
none
none
amount
number
false
none
none
applyTime
string
false
none
none
coin
string
false
none
none
completeTime
string
false
none
none
confirmNo
integer(int32)
false
none
none
extensionInfo
string
false
none
none
id
string
false
none
none
info
string
false
none
none
network
string
false
none
none
status
integer(int32)
false
none
none
transactionFee
number
false
none
none
transferType
integer(int32)
false
none
none
txId
string
false
none
none
txKey
string
false
none
none
walletType
integer(int32)
false
none
none
withdrawOrderId
string
false
none
none


---

## Page 324

sapi-v7.4.md
2024-05-08
324 / 419
WithdrawNftResponse
{ 
  "batchNumber": "string", 
  "reason": "string", 
  "result": true 
} 
 
WithdrawNftResponse
42.607. Properties
Name
Type
Required
Restrictions
Description
batchNumber
string
false
none
none
reason
string
false
none
none
result
boolean
false
none
none
WrapHistory
{ 
  "exchangeRate": "string", 
  "fromAmount": 0, 
  "fromAsset": "string", 
  "status": "string", 
  "time": 0, 
  "toAmount": 0, 
  "toAsset": "string" 
} 
 
WrapHistory
42.608. Properties
Name
Type
Required
Restrictions
Description
exchangeRate
string
false
none
none
fromAmount
number
false
none
none
fromAsset
string
false
none
none
status
string
false
none
none
time
integer(int64)
false
none
none
toAmount
number
false
none
none
toAsset
string
false
none
none
WrapHistoryResponse
{ 
  "rows": [ 
    { 
      "exchangeRate": "string", 
      "fromAmount": 0, 
      "fromAsset": "string", 
      "status": "string", 
      "time": 0, 
      "toAmount": 0, 
      "toAsset": "string" 
    } 
  ], 
  "total": 0 
} 
 
WrapHistoryResponse
42.609. Properties


---

## Page 325

sapi-v7.4.md
2024-05-08
325 / 419
Name
Type
Required
Restrictions
Description
rows
[WrapHistory]
false
none
none
total
integer(int64)
false
none
none
WrapResponse
{ 
  "exchangeRate": "string", 
  "success": true, 
  "wbethAmount": 0 
} 
 
WrapResponse
42.610. Properties
Name
Type
Required
Restrictions
Description
exchangeRate
string
false
none
none
success
boolean
false
none
none
wbethAmount
number
false
none
none
APIResponse_CloudRebateVo_
{ 
  "code": "string", 
  "data": { 
    "asset": "string", 
    "delta": 0, 
    "status": 0, 
    "tranId": 0 
  }, 
  "errorData": {}, 
  "params": [ 
    {} 
  ], 
  "status": "ERROR", 
  "subData": {}, 
  "type": "GENERAL" 
} 
 
APIResponse«CloudRebateVo»
42.611. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
data
CloudRebateVo
false
none
none
errorData
object
false
none
none
params
[object]
false
none
none
status
string
false
none
none
subData
object
false
none
none
type
string
false
none
none
42.611.1. Enumerated Values
Property
Value
status
ERROR
status
OK
type
GENERAL
type
SYS


---

## Page 326

sapi-v7.4.md
2024-05-08
326 / 419
Property
Value
type
VALID
APIResponse_List_CloudOrderVo_
{ 
  "code": "string", 
  "data": [ 
    { 
      "clientOrderId": "string", 
      "cummulativeQuoteQty": 0, 
      "executedQty": 0, 
      "icebergQty": 0, 
      "isWorking": true, 
      "orderId": 0, 
      "orderListId": 0, 
      "origQty": 0, 
      "origQuoteOrderQty": 0, 
      "price": 0, 
      "side": "string", 
      "status": "string", 
      "stopPrice": 0, 
      "symbol": "string", 
      "time": 0, 
      "timeInForce": "string", 
      "type": "string", 
      "updateTime": 0 
    } 
  ], 
  "errorData": {}, 
  "params": [ 
    {} 
  ], 
  "status": "ERROR", 
  "subData": {}, 
  "type": "GENERAL" 
} 
 
APIResponse«List«CloudOrderVo»»
42.612. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
data
[CloudOrderVo]
false
none
none
errorData
object
false
none
none
params
[object]
false
none
none
status
string
false
none
none
subData
object
false
none
none
type
string
false
none
none
42.612.1. Enumerated Values
Property
Value
status
ERROR
status
OK
type
GENERAL
type
SYS
type
VALID
APIResponse_List_CloudTradeVo_
{ 
  "code": "string", 


---

## Page 327

sapi-v7.4.md
2024-05-08
327 / 419
  "data": [ 
    { 
      "commission": 0, 
      "commissionAsset": "string", 
      "id": 0, 
      "isBestMatch": true, 
      "isBuyer": true, 
      "isMaker": true, 
      "orderId": 0, 
      "orderListId": 0, 
      "price": 0, 
      "qty": 0, 
      "quoteQty": 0, 
      "symbol": "string", 
      "time": 0 
    } 
  ], 
  "errorData": {}, 
  "params": [ 
    {} 
  ], 
  "status": "ERROR", 
  "subData": {}, 
  "type": "GENERAL" 
} 
 
APIResponse«List«CloudTradeVo»»
42.613. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
data
[CloudTradeVo]
false
none
none
errorData
object
false
none
none
params
[object]
false
none
none
status
string
false
none
none
subData
object
false
none
none
type
string
false
none
none
42.613.1. Enumerated Values
Property
Value
status
ERROR
status
OK
type
GENERAL
type
SYS
type
VALID
APIResponse_MarketMakersResponse_
{ 
  "code": "string", 
  "data": { 
    "cmMmLevel": "string", 
    "cmRebates": 0, 
    "curCmTaker": 0, 
    "curMmStatus": "string", 
    "curSpotTaker": 0, 
    "curUmTaker": 0, 
    "curVipLevel": 0, 
    "futuresVol30d": 0, 
    "ifCmMm": true, 
    "ifSpotMm": true, 
    "ifUmMm": true, 
    "spotMmLevel": "string", 
    "spotRebates": 0, 
    "spotVol30d": 0, 


---

## Page 328

sapi-v7.4.md
2024-05-08
328 / 419
    "umMmLevel": "string", 
    "umRebates": 0, 
    "userId": 0 
  }, 
  "errorData": {}, 
  "params": [ 
    {} 
  ], 
  "status": "ERROR", 
  "subData": {}, 
  "type": "GENERAL" 
} 
 
APIResponse«MarketMakersResponse»
42.614. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
data
MarketMakersResponse
false
none
none
errorData
object
false
none
none
params
[object]
false
none
none
status
string
false
none
none
subData
object
false
none
none
type
string
false
none
none
42.614.1. Enumerated Values
Property
Value
status
ERROR
status
OK
type
GENERAL
type
SYS
type
VALID
APIResponse_Page_VIP_Portal_Report_Config_Model_
{ 
  "code": "string", 
  "data": { 
    "current": 0, 
    "hitCount": true, 
    "optimizeCountSql": true, 
    "orders": [ 
      { 
        "asc": true, 
        "column": "string" 
      } 
    ], 
    "pages": 0, 
    "records": [ 
      { 
        "businessType": "string", 
        "fileTypes": [ 
          "string" 
        ], 
        "reportFields": [ 
          "string" 
        ], 
        "reportType": "string" 
      } 
    ], 
    "searchCount": true, 
    "size": 0, 
    "total": 0 
  }, 
  "errorData": {}, 


---

## Page 329

sapi-v7.4.md
2024-05-08
329 / 419
  "params": [ 
    {} 
  ], 
  "status": "ERROR", 
  "subData": {}, 
  "type": "GENERAL" 
} 
 
APIResponse«Page«VIP Portal Report Config Model»»
42.615. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
data
Page_VIP_Portal_Report_Config_Model_
false
none
none
errorData
object
false
none
none
params
[object]
false
none
none
status
string
false
none
none
subData
object
false
none
none
type
string
false
none
none
42.615.1. Enumerated Values
Property
Value
status
ERROR
status
OK
type
GENERAL
type
SYS
type
VALID
APIResponse_Page_VIP_Portal_Report_Item_Model_
{ 
  "code": "string", 
  "data": { 
    "current": 0, 
    "hitCount": true, 
    "optimizeCountSql": true, 
    "orders": [ 
      { 
        "asc": true, 
        "column": "string" 
      } 
    ], 
    "pages": 0, 
    "records": [ 
      { 
        "businessType": "string", 
        "createByUid": "string", 
        "dbCreateTime": "2019-08-24T14:15:22Z", 
        "dbModifyTime": "2019-08-24T14:15:22Z", 
        "emails": [ 
          "string" 
        ], 
        "endDate": "string", 
        "fileType": "string", 
        "pdfLink": "string", 
        "reportName": "string", 
        "reportType": "string", 
        "reportUrl": "string", 
        "s3Link": "string", 
        "source": "string", 
        "startDate": "string", 
        "status": 0, 
        "timezone": "string", 
        "url": "string", 
        "userId": "string" 


---

## Page 330

sapi-v7.4.md
2024-05-08
330 / 419
      } 
    ], 
    "searchCount": true, 
    "size": 0, 
    "total": 0 
  }, 
  "errorData": {}, 
  "params": [ 
    {} 
  ], 
  "status": "ERROR", 
  "subData": {}, 
  "type": "GENERAL" 
} 
 
APIResponse«Page«VIP Portal Report Item Model»»
42.616. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
data
Page_VIP_Portal_Report_Item_Model_
false
none
none
errorData
object
false
none
none
params
[object]
false
none
none
status
string
false
none
none
subData
object
false
none
none
type
string
false
none
none
42.616.1. Enumerated Values
Property
Value
status
ERROR
status
OK
type
GENERAL
type
SYS
type
VALID
APIResponse_UserTotalAssetResponse_
{ 
  "code": "string", 
  "data": { 
    "endDay": "2019-08-24", 
    "md5Uid": "string", 
    "quoteAsset": "string", 
    "startDay": "2019-08-24", 
    "userId": 0, 
    "userTotalAssetModels": [ 
      { 
        "card": 0, 
        "delivery": 0, 
        "future": 0, 
        "inValid": true, 
        "isolatedMargin": 0, 
        "main": 0, 
        "margin": 0, 
        "saving": 0, 
        "time": "2019-08-24T14:15:22Z", 
        "timestamp": 0, 
        "toption": 0, 
        "total": 0 
      } 
    ] 
  }, 
  "errorData": {}, 
  "params": [ 
    {} 


---

## Page 331

sapi-v7.4.md
2024-05-08
331 / 419
  ], 
  "status": "ERROR", 
  "subData": {}, 
  "type": "GENERAL" 
} 
 
APIResponse«UserTotalAssetResponse»
42.617. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
data
UserTotalAssetResponse
false
none
none
errorData
object
false
none
none
params
[object]
false
none
none
status
string
false
none
none
subData
object
false
none
none
type
string
false
none
none
42.617.1. Enumerated Values
Property
Value
status
ERROR
status
OK
type
GENERAL
type
SYS
type
VALID
APIResponse_VIP_Portal_Report_Item_Model_
{ 
  "code": "string", 
  "data": { 
    "businessType": "string", 
    "createByUid": "string", 
    "dbCreateTime": "2019-08-24T14:15:22Z", 
    "dbModifyTime": "2019-08-24T14:15:22Z", 
    "emails": [ 
      "string" 
    ], 
    "endDate": "string", 
    "fileType": "string", 
    "pdfLink": "string", 
    "reportName": "string", 
    "reportType": "string", 
    "reportUrl": "string", 
    "s3Link": "string", 
    "source": "string", 
    "startDate": "string", 
    "status": 0, 
    "timezone": "string", 
    "url": "string", 
    "userId": "string" 
  }, 
  "errorData": {}, 
  "params": [ 
    {} 
  ], 
  "status": "ERROR", 
  "subData": {}, 
  "type": "GENERAL" 
} 
 
APIResponse«VIP Portal Report Item Model»


---

## Page 332

sapi-v7.4.md
2024-05-08
332 / 419
42.618. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
data
VIP_Portal_Report_Item_Model
false
none
none
errorData
object
false
none
none
params
[object]
false
none
none
status
string
false
none
none
subData
object
false
none
none
type
string
false
none
none
42.618.1. Enumerated Values
Property
Value
status
ERROR
status
OK
type
GENERAL
type
SYS
type
VALID
APIResponse_boolean_
{ 
  "code": "string", 
  "data": true, 
  "errorData": {}, 
  "params": [ 
    {} 
  ], 
  "status": "ERROR", 
  "subData": {}, 
  "type": "GENERAL" 
} 
 
APIResponse«boolean»
42.619. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
data
boolean
false
none
none
errorData
object
false
none
none
params
[object]
false
none
none
status
string
false
none
none
subData
object
false
none
none
type
string
false
none
none
42.619.1. Enumerated Values
Property
Value
status
ERROR
status
OK
type
GENERAL
type
SYS
type
VALID
APIResponse_


---

## Page 333

sapi-v7.4.md
2024-05-08
333 / 419
{ 
  "code": "string", 
  "data": { 
    "data": [ 
      { 
        "amount": 0, 
        "asset": "string", 
        "type": 0, 
        "updateTime": "2019-08-24T14:15:22Z" 
      } 
    ], 
    "page": 0, 
    "totalPageNum": 0, 
    "totalRecords": 0 
  }, 
  "errorData": {}, 
  "params": [ 
    {} 
  ], 
  "status": "ERROR", 
  "subData": {}, 
  "type": "GENERAL" 
} 
 
APIResponse«⽤户佣⾦收益明细（⽤于税务）返回结果»
42.620. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
none
data
_4
false
none
none
errorData
object
false
none
none
params
[object]
false
none
none
status
string
false
none
none
subData
object
false
none
none
type
string
false
none
none
42.620.1. Enumerated Values
Property
Value
status
ERROR
status
OK
type
GENERAL
type
SYS
type
VALID
AccountSnapshotVo_object_
{ 
  "data": {}, 
  "type": "string", 
  "updateTime": 0 
} 
 
AccountSnapshotVo«object»
42.621. Properties
Name
Type
Required
Restrictions
Description
data
object
false
none
none
type
string
false
none
none


---

## Page 334

sapi-v7.4.md
2024-05-08
334 / 419
Name
Type
Required
Restrictions
Description
updateTime
integer(int64)
false
none
none
AmountResp_bigdecimal_
{ 
  "amount": 0 
} 
 
AmountResp«bigdecimal»
42.622. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
none
Asset_detail
{ 
  "asset": "string", 
  "decimalScale": 0, 
  "iconUrl": "string", 
  "name": "string" 
} 
 
Asset detail
42.623. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
Digital currency abbreviation, e.g.: BTC, BNB
decimalScale
integer(int32)
false
none
Decimal precision scale
iconUrl
string
false
none
Digital currency icon URL
name
string
false
none
Digital currency full name
C2C_CancelOrderReq
{ 
  "orderCancelAdditionalInfo": "string", 
  "orderCancelReasonCode": 0, 
  "orderNumber": "string" 
} 
 
C2C CancelOrderReq
42.624. Properties
Name
Type
Required
Restrictions
Description
orderCancelAdditionalInfo
string
false
none
Order cancellation, additional reason, when other reasons are selected, description of
additional reason is provided
orderCancelReasonCode
integer(int32)
true
none
Order cancellation reason code (1: I change mind, 2: I don't meet seller's requirement,
3: Seller asking extra fee, 4: Seller's payment method issue, 5: Other, 6: Seller cannot
release)
orderNumber
string
false
none
Order No
CommonPageRet_AdDetailResp_
{ 
  "code": "string", 
  "data": [ 


---

## Page 335

sapi-v7.4.md
2024-05-08
335 / 419
    { 
      "advNo": "string", 
      "advStatus": 0, 
      "advUpdateTime": "2019-08-24T14:15:22Z", 
      "advVisibleRet": { 
        "freeAmountVisible": 0, 
        "orderFlowVisible": 0, 
        "surplusAmountVisible": 0, 
        "userSetVisible": 0 
      }, 
      "asset": "string", 
      "assetLogo": "string", 
      "assetScale": 0, 
      "assetVo": { 
        "asset": "string", 
        "decimalScale": 0, 
        "iconUrl": "string", 
        "name": "string" 
      }, 
      "autoReplyMsg": "string", 
      "buyerBtcPositionLimit": 0, 
      "buyerKycLimit": 0, 
      "buyerRegDaysLimit": 0, 
      "classify": "string", 
      "commissionRate": 0, 
      "createTime": "2019-08-24T14:15:22Z", 
      "currencyRate": 0, 
      "dynamicMaxSingleTransAmount": 0, 
      "dynamicMaxSingleTransQuantity": 0, 
      "fiatScale": 0, 
      "fiatSymbol": "string", 
      "fiatUnit": "string", 
      "fiatVo": { 
        "countryCode": "string", 
        "currencyCode": "string", 
        "currencyScale": 0, 
        "currencySymbol": "string", 
        "iconUrl": "string", 
        "priceScale": 0 
      }, 
      "initAmount": 0, 
      "isTradable": true, 
      "maxSingleTransAmount": 0, 
      "maxSingleTransQuantity": 0, 
      "minSingleTransAmount": 0, 
      "minSingleTransQuantity": 0, 
      "offlineReason": "string", 
      "payTimeLimit": 0, 
      "price": 0, 
      "priceFloatingRatio": 0, 
      "priceScale": 0, 
      "priceType": 0, 
      "rateFloatingRatio": 0, 
      "remarks": "string", 
      "surplusAmount": 0, 
      "takerAdditionalKycRequired": 0, 
      "tradableQuantity": 0, 
      "tradeMethodCommissionRateVoList": [ 
        { 
          "commissionRate": 0, 
          "tradeMethodIdentifier": "string", 
          "tradeMethodName": "string" 
        } 
      ], 
      "tradeMethods": [ 
        { 
          "iconUrlColor": "string", 
          "identifier": "string", 
          "payAccount": "string", 
          "payBank": "string", 
          "payId": 0, 
          "paySubBank": "string", 
          "payType": "string", 
          "tradeMethodName": "string" 
        } 
      ], 
      "tradeType": "string", 
      "userAllTradeCountMax": 0, 
      "userAllTradeCountMin": 0, 
      "userBuyTradeCountMax": 0, 
      "userBuyTradeCountMin": 0, 


---

## Page 336

sapi-v7.4.md
2024-05-08
336 / 419
      "userSellTradeCountMax": 0, 
      "userSellTradeCountMin": 0, 
      "userTradeCompleteCountMin": 0, 
      "userTradeCompleteRateFilterTime": 0, 
      "userTradeCompleteRateMin": 0, 
      "userTradeCountFilterTime": 0, 
      "userTradeType": 0, 
      "userTradeVolumeAsset": "string", 
      "userTradeVolumeFilterTime": 0, 
      "userTradeVolumeMax": 0, 
      "userTradeVolumeMin": 0 
    } 
  ], 
  "message": "string", 
  "success": true, 
  "total": 0 
} 
 
CommonPageRet«AdDetailResp»
42.625. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
[AdDetailResp]
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
total
integer(int64)
false
none
none
CommonPageRet_AdSearchResp_
{ 
  "code": "string", 
  "data": [ 
    { 
      "adv": { 
        "advNo": "string", 
        "advStatus": 0, 
        "advUpdateTime": "2019-08-24T14:15:22Z", 
        "advVisibleRet": { 
          "freeAmountVisible": 0, 
          "orderFlowVisible": 0, 
          "surplusAmountVisible": 0, 
          "userSetVisible": 0 
        }, 
        "asset": "string", 
        "assetLogo": "string", 
        "assetScale": 0, 
        "assetVo": { 
          "asset": "string", 
          "decimalScale": 0, 
          "iconUrl": "string", 
          "name": "string" 
        }, 
        "autoReplyMsg": "string", 
        "buyerBtcPositionLimit": 0, 
        "buyerKycLimit": 0, 
        "buyerRegDaysLimit": 0, 
        "classify": "string", 
        "commissionRate": 0, 
        "createTime": "2019-08-24T14:15:22Z", 
        "currencyRate": 0, 
        "dynamicMaxSingleTransAmount": 0, 
        "dynamicMaxSingleTransQuantity": 0, 
        "fiatScale": 0, 
        "fiatSymbol": "string", 
        "fiatUnit": "string", 
        "fiatVo": { 
          "countryCode": "string", 
          "currencyCode": "string", 
          "currencyScale": 0, 
          "currencySymbol": "string", 
          "iconUrl": "string", 


---

## Page 337

sapi-v7.4.md
2024-05-08
337 / 419
          "priceScale": 0 
        }, 
        "initAmount": 0, 
        "isTradable": true, 
        "maxSingleTransAmount": 0, 
        "maxSingleTransQuantity": 0, 
        "minSingleTransAmount": 0, 
        "minSingleTransQuantity": 0, 
        "offlineReason": "string", 
        "payTimeLimit": 0, 
        "price": 0, 
        "priceFloatingRatio": 0, 
        "priceScale": 0, 
        "priceType": 0, 
        "rateFloatingRatio": 0, 
        "remarks": "string", 
        "surplusAmount": 0, 
        "takerAdditionalKycRequired": 0, 
        "tradableQuantity": 0, 
        "tradeMethodCommissionRateVoList": [ 
          { 
            "commissionRate": null, 
            "tradeMethodIdentifier": null, 
            "tradeMethodName": null 
          } 
        ], 
        "tradeMethods": [ 
          { 
            "iconUrlColor": null, 
            "identifier": null, 
            "payAccount": null, 
            "payBank": null, 
            "payId": null, 
            "paySubBank": null, 
            "payType": null, 
            "tradeMethodName": null 
          } 
        ], 
        "tradeType": "string", 
        "userAllTradeCountMax": 0, 
        "userAllTradeCountMin": 0, 
        "userBuyTradeCountMax": 0, 
        "userBuyTradeCountMin": 0, 
        "userSellTradeCountMax": 0, 
        "userSellTradeCountMin": 0, 
        "userTradeCompleteCountMin": 0, 
        "userTradeCompleteRateFilterTime": 0, 
        "userTradeCompleteRateMin": 0, 
        "userTradeCountFilterTime": 0, 
        "userTradeType": 0, 
        "userTradeVolumeAsset": "string", 
        "userTradeVolumeFilterTime": 0, 
        "userTradeVolumeMax": 0, 
        "userTradeVolumeMin": 0 
      }, 
      "advertiser": { 
        "advConfirmTime": 0, 
        "email": "string", 
        "margin": 0, 
        "marginUnit": "string", 
        "mobile": "string", 
        "monthFinishRate": 0, 
        "monthOrderCount": 0, 
        "nickName": "string", 
        "orderCount": 0, 
        "realName": "string", 
        "registrationTime": "2019-08-24T14:15:22Z", 
        "tagIconUrls": [ 
          "string" 
        ], 
        "userNo": "string", 
        "userType": "string" 
      } 
    } 
  ], 
  "message": "string", 
  "success": true, 
  "total": 0 
} 
 


---

## Page 338

sapi-v7.4.md
2024-05-08
338 / 419
CommonPageRet«AdSearchResp»
42.626. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
[AdSearchResp]
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
total
integer(int64)
false
none
none
CommonPageRet_OrderMatchListResp_
{ 
  "code": "string", 
  "data": [ 
    { 
      "additionalKycVerify": 0, 
      "advNo": "string", 
      "amount": "string", 
      "asset": "string", 
      "assetTicketSize": "string", 
      "buyerNickname": "string", 
      "chatUnreadCount": 0, 
      "commission": 0, 
      "commissionRate": 0, 
      "confirmPayEndTime": "2019-08-24T14:15:22Z", 
      "createTime": "2019-08-24T14:15:22Z", 
      "currencyTicketSize": "string", 
      "fiat": "string", 
      "fiatSymbol": "string", 
      "notifyPayEndTime": "2019-08-24T14:15:22Z", 
      "orderNumber": "string", 
      "orderStatus": 0, 
      "priceTicketSize": "string", 
      "sellerNickname": "string", 
      "takerAmount": 0, 
      "takerCommission": 0, 
      "takerCommissionRate": 0, 
      "totalPrice": "string", 
      "tradeMethodCommissionRateVoList": [ 
        { 
          "commissionRate": 0, 
          "tradeMethodIdentifier": "string", 
          "tradeMethodName": "string" 
        } 
      ], 
      "tradeType": "string" 
    } 
  ], 
  "message": "string", 
  "success": true, 
  "total": 0 
} 
 
CommonPageRet«OrderMatchListResp»
42.627. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
[OrderMatchListResp]
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
total
integer(int64)
false
none
none
CommonPageRet_RetrieveChatMessagesWithPaginationResp_


---

## Page 339

sapi-v7.4.md
2024-05-08
339 / 419
{ 
  "code": "string", 
  "data": [ 
    { 
      "content": "string", 
      "createTime": "2019-08-24T14:15:22Z", 
      "fromNickName": "string", 
      "height": 0, 
      "id": 0, 
      "imageType": "string", 
      "imageUrl": "string", 
      "orderNo": "string", 
      "self": true, 
      "status": "read", 
      "thumbnailUrl": "string", 
      "type": "auto_reply", 
      "uuid": "string", 
      "width": 0 
    } 
  ], 
  "message": "string", 
  "success": true, 
  "total": 0 
} 
 
CommonPageRet«RetrieveChatMessagesWithPaginationResp»
42.628. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
[RetrieveChatMessagesWithPaginationResp]
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
total
integer(int64)
false
none
none
CommonPageRet_User_Order_History_
{ 
  "code": "string", 
  "data": [ 
    { 
      "additionalKycVerify": 0, 
      "advNo": "string", 
      "advertisementRole": "string", 
      "amount": "string", 
      "asset": "string", 
      "commission": 0, 
      "counterPartNickName": "string", 
      "createTime": "2019-08-24T14:15:22Z", 
      "fiat": "string", 
      "fiatSymbol": "string", 
      "orderNumber": "string", 
      "orderStatus": "string", 
      "payMethodName": "string", 
      "takerAmount": 0, 
      "takerCommission": 0, 
      "takerCommissionRate": 0, 
      "totalPrice": "string", 
      "tradeType": "string", 
      "unitPrice": 0 
    } 
  ], 
  "message": "string", 
  "success": true, 
  "total": 0 
} 
 
CommonPageRet«User Order History»


---

## Page 340

sapi-v7.4.md
2024-05-08
340 / 419
42.629. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
[User_Order_History]
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
total
integer(int64)
false
none
none
CommonPageRet_
{ 
  "code": "string", 
  "data": [ 
    { 
      "bgColor": "string", 
      "chatNeed": 0, 
      "createTime": "2019-08-24T14:15:22Z", 
      "iconUrlColor": "string", 
      "iconUrlGray": "string", 
      "id": 0, 
      "identifier": "string", 
      "isOnline": 0, 
      "isRecommended": 0, 
      "isVisible": 0, 
      "multiAllow": 0, 
      "name": "string", 
      "nameKey": "string", 
      "remark": "string", 
      "risk": "string", 
      "riskKey": "string", 
      "riskLevel": 0, 
      "sequence": 0, 
      "shortName": "string", 
      "shortNameKey": "string", 
      "tradeMethodCode": 0, 
      "typeCode": "string", 
      "typeName": "string", 
      "updateTime": "2019-08-24T14:15:22Z" 
    } 
  ], 
  "message": "string", 
  "success": true, 
  "total": 0 
} 
 
CommonPageRet«交易⽅式»
42.630. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
[_]
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
total
integer(int64)
false
none
none
CommonPageRet_2
{ 
  "code": "string", 
  "data": [ 
    { 
      "createTime": "2019-08-24T14:15:22Z", 
      "cryptoCurrency": "string", 
      "fiatCurrency": "string", 
      "obtainAmount": "string", 


---

## Page 341

sapi-v7.4.md
2024-05-08
341 / 419
      "orderNo": "string", 
      "paymentMethod": "string", 
      "price": "string", 
      "sourceAmount": "string", 
      "status": "string", 
      "totalFee": "string", 
      "updateTime": "2019-08-24T14:15:22Z" 
    } 
  ], 
  "message": "string", 
  "success": true, 
  "total": 0 
} 
 
CommonPageRet«⽤户买卖订单详情»
42.631. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
[_3]
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
total
integer(int64)
false
none
none
CommonPageRet_3
{ 
  "code": "string", 
  "data": [ 
    { 
      "amount": "string", 
      "createTime": "2019-08-24T14:15:22Z", 
      "fiatCurrency": "string", 
      "indicatedAmount": "string", 
      "method": "string", 
      "orderNo": "string", 
      "status": "string", 
      "totalFee": "string", 
      "updateTime": "2019-08-24T14:15:22Z" 
    } 
  ], 
  "message": "string", 
  "success": true, 
  "total": 0 
} 
 
CommonPageRet«⽤户充提订单详情»
42.632. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
[_5]
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
total
integer(int64)
false
none
none
CommonRet_AdDetailResp_
{ 
  "code": "string", 
  "data": { 
    "advNo": "string", 
    "advStatus": 0, 


---

## Page 342

sapi-v7.4.md
2024-05-08
342 / 419
    "advUpdateTime": "2019-08-24T14:15:22Z", 
    "advVisibleRet": { 
      "freeAmountVisible": 0, 
      "orderFlowVisible": 0, 
      "surplusAmountVisible": 0, 
      "userSetVisible": 0 
    }, 
    "asset": "string", 
    "assetLogo": "string", 
    "assetScale": 0, 
    "assetVo": { 
      "asset": "string", 
      "decimalScale": 0, 
      "iconUrl": "string", 
      "name": "string" 
    }, 
    "autoReplyMsg": "string", 
    "buyerBtcPositionLimit": 0, 
    "buyerKycLimit": 0, 
    "buyerRegDaysLimit": 0, 
    "classify": "string", 
    "commissionRate": 0, 
    "createTime": "2019-08-24T14:15:22Z", 
    "currencyRate": 0, 
    "dynamicMaxSingleTransAmount": 0, 
    "dynamicMaxSingleTransQuantity": 0, 
    "fiatScale": 0, 
    "fiatSymbol": "string", 
    "fiatUnit": "string", 
    "fiatVo": { 
      "countryCode": "string", 
      "currencyCode": "string", 
      "currencyScale": 0, 
      "currencySymbol": "string", 
      "iconUrl": "string", 
      "priceScale": 0 
    }, 
    "initAmount": 0, 
    "isTradable": true, 
    "maxSingleTransAmount": 0, 
    "maxSingleTransQuantity": 0, 
    "minSingleTransAmount": 0, 
    "minSingleTransQuantity": 0, 
    "offlineReason": "string", 
    "payTimeLimit": 0, 
    "price": 0, 
    "priceFloatingRatio": 0, 
    "priceScale": 0, 
    "priceType": 0, 
    "rateFloatingRatio": 0, 
    "remarks": "string", 
    "surplusAmount": 0, 
    "takerAdditionalKycRequired": 0, 
    "tradableQuantity": 0, 
    "tradeMethodCommissionRateVoList": [ 
      { 
        "commissionRate": 0, 
        "tradeMethodIdentifier": "string", 
        "tradeMethodName": "string" 
      } 
    ], 
    "tradeMethods": [ 
      { 
        "iconUrlColor": "string", 
        "identifier": "string", 
        "payAccount": "string", 
        "payBank": "string", 
        "payId": 0, 
        "paySubBank": "string", 
        "payType": "string", 
        "tradeMethodName": "string" 
      } 
    ], 
    "tradeType": "string", 
    "userAllTradeCountMax": 0, 
    "userAllTradeCountMin": 0, 
    "userBuyTradeCountMax": 0, 
    "userBuyTradeCountMin": 0, 
    "userSellTradeCountMax": 0, 
    "userSellTradeCountMin": 0, 
    "userTradeCompleteCountMin": 0, 


---

## Page 343

sapi-v7.4.md
2024-05-08
343 / 419
    "userTradeCompleteRateFilterTime": 0, 
    "userTradeCompleteRateMin": 0, 
    "userTradeCountFilterTime": 0, 
    "userTradeType": 0, 
    "userTradeVolumeAsset": "string", 
    "userTradeVolumeFilterTime": 0, 
    "userTradeVolumeMax": 0, 
    "userTradeVolumeMin": 0 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«AdDetailResp»
42.633. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
AdDetailResp
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_AdUpdateStatusResp_
{ 
  "code": "string", 
  "data": { 
    "failList": [ 
      { 
        "advNo": "string", 
        "errorCode": "string", 
        "errorMsg": "string" 
      } 
    ], 
    "status": true 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«AdUpdateStatusResp»
42.634. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
AdUpdateStatusResp
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_ChatCredentialResp_
{ 
  "code": "string", 
  "data": { 
    "chatWssUrl": "string", 
    "listenKey": "string", 
    "listenToken": "string" 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«ChatCredentialResp»


---

## Page 344

sapi-v7.4.md
2024-05-08
344 / 419
42.635. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
ChatCredentialResp
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_FetchImageUploadUrlRet_
{ 
  "code": "string", 
  "data": { 
    "imageUrl": "string", 
    "uploadUrl": "string" 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«FetchImageUploadUrlRet»
42.636. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
FetchImageUploadUrlRet
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_FiatUserDetailResp_
{ 
  "code": "string", 
  "data": { 
    "bindMobileStatus": "BIND", 
    "businessStatus": 0, 
    "countryCode": "string", 
    "existsNickname": true, 
    "fiatProtocolConfirm": true, 
    "isSubUser": true, 
    "isUserGoogle": true, 
    "isUserMobile": true, 
    "kycFullName": "string", 
    "kycPassed": true, 
    "kycType": 0, 
    "nickname": "string", 
    "overComplained": 0, 
    "registerDays": 0, 
    "userKycStatus": "NOTVERIFIED" 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«FiatUserDetailResp»
42.637. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
FiatUserDetailResp
false
none
返回的具体数据信息
message
string
false
none
消息内容


---

## Page 345

sapi-v7.4.md
2024-05-08
345 / 419
Name
Type
Required
Restrictions
Description
success
boolean
false
none
none
CommonRet_GetFiatChannelProductSelectorResponse_
{ 
  "code": "string", 
  "data": { 
    "buySelector": [ 
      { 
        "assetCode": "string", 
        "assetName": "string", 
        "dailyMaxLimit": 0, 
        "exchangeRate": "string", 
        "expireTime": 0, 
        "forceToOthers": true, 
        "hot": true, 
        "isAlreadyBuy": 0, 
        "langSorts": [ 
          "string" 
        ], 
        "logoUrl": "string", 
        "order": 0, 
        "perTimeMaxLimit": 0, 
        "perTimeMinLimit": 0, 
        "showRemark": true, 
        "size": "string", 
        "stable": true, 
        "subSelector": [ 
          { 
            "assetCode": null, 
            "assetName": null, 
            "dailyMaxLimit": null, 
            "exchangeRate": null, 
            "expireTime": null, 
            "forceToOthers": null, 
            "hot": null, 
            "isAlreadyBuy": null, 
            "langSorts": null, 
            "logoUrl": null, 
            "order": null, 
            "perTimeMaxLimit": null, 
            "perTimeMinLimit": null, 
            "showRemark": null, 
            "size": null, 
            "stable": null, 
            "subSelector": null 
          } 
        ] 
      } 
    ], 
    "sellSelector": [ 
      { 
        "assetCode": "string", 
        "assetName": "string", 
        "dailyMaxLimit": 0, 
        "exchangeRate": "string", 
        "expireTime": 0, 
        "forceToOthers": true, 
        "hot": true, 
        "isAlreadyBuy": 0, 
        "langSorts": [ 
          "string" 
        ], 
        "logoUrl": "string", 
        "order": 0, 
        "perTimeMaxLimit": 0, 
        "perTimeMinLimit": 0, 
        "showRemark": true, 
        "size": "string", 
        "stable": true, 
        "subSelector": [ 
          { 
            "assetCode": null, 
            "assetName": null, 
            "dailyMaxLimit": null, 
            "exchangeRate": null, 
            "expireTime": null, 


---

## Page 346

sapi-v7.4.md
2024-05-08
346 / 419
            "forceToOthers": null, 
            "hot": null, 
            "isAlreadyBuy": null, 
            "langSorts": null, 
            "logoUrl": null, 
            "order": null, 
            "perTimeMaxLimit": null, 
            "perTimeMinLimit": null, 
            "showRemark": null, 
            "size": null, 
            "stable": null, 
            "subSelector": null 
          } 
        ] 
      } 
    ] 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«GetFiatChannelProductSelectorResponse»
42.638. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
GetFiatChannelProductSelectorResponse
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_List_AdReferencePriceResp_
{ 
  "code": "string", 
  "data": [ 
    { 
      "asset": "string", 
      "assetScale": 0, 
      "currency": "string", 
      "currencyScale": 0, 
      "currencySymbol": "string", 
      "priceScale": 0, 
      "referencePrice": 0 
    } 
  ], 
  "message": "string", 
  "success": true 
} 
 
CommonRet«List«AdReferencePriceResp»»
42.639. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
[AdReferencePriceResp]
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_List_PayMethodResp_
{ 
  "code": "string", 
  "data": [ 
    { 
      "advCount": 0, 


---

## Page 347

sapi-v7.4.md
2024-05-08
347 / 419
      "createTime": "2019-08-24T14:15:22Z", 
      "currentPayAmount": 0, 
      "fieldList": [ 
        { 
          "createTime": "2019-08-24T14:15:22Z", 
          "errorKey": "string", 
          "errorWord": "string", 
          "fieldContentType": "string", 
          "fieldId": "string", 
          "fieldName": "string", 
          "fieldTitle": "string", 
          "fieldTitleKey": "string", 
          "fieldValue": "string", 
          "hintKey": "string", 
          "hintWord": "string", 
          "id": 0, 
          "isCopyable": 0, 
          "isDisplay": 0, 
          "isEncrypt": 0, 
          "isRequired": 0, 
          "lengthLimit": 0, 
          "restrictionType": 0, 
          "sequence": 0, 
          "status": 0, 
          "updateTime": "2019-08-24T14:15:22Z" 
        } 
      ], 
      "forbidReason": "string", 
      "id": 0, 
      "isRemoved": 0, 
      "mainUserId": 0, 
      "payAccount": "string", 
      "payBank": "string", 
      "payLimit": 0, 
      "payLimitUnit": "string", 
      "payStatus": "ACTIVE", 
      "paySubBank": "string", 
      "payType": "ALIPAY", 
      "payee": "string", 
      "qrCodePath": "string", 
      "tradeMethod": { 
        "bgColor": "string", 
        "chatNeed": 0, 
        "createTime": "2019-08-24T14:15:22Z", 
        "iconUrlColor": "string", 
        "iconUrlGray": "string", 
        "id": 0, 
        "identifier": "string", 
        "isOnline": 0, 
        "isRecommended": 0, 
        "isVisible": 0, 
        "multiAllow": 0, 
        "name": "string", 
        "nameKey": "string", 
        "remark": "string", 
        "risk": "string", 
        "riskKey": "string", 
        "riskLevel": 0, 
        "sequence": 0, 
        "shortName": "string", 
        "shortNameKey": "string", 
        "tradeMethodCode": 0, 
        "typeCode": "string", 
        "typeName": "string", 
        "updateTime": "2019-08-24T14:15:22Z" 
      }, 
      "tradeMethodIdentifier": "string", 
      "updateTime": "2019-08-24T14:15:22Z", 
      "userId": 0 
    } 
  ], 
  "message": "string", 
  "success": true 
} 
 
CommonRet«List«PayMethodResp»»
42.640. Properties


---

## Page 348

sapi-v7.4.md
2024-05-08
348 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
[PayMethodResp]
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_List_Recurring_Buy_Order_Payments_
{ 
  "code": "string", 
  "data": [ 
    { 
      "contractNo": "string", 
      "contractSerialNo": "string", 
      "createTime": "2019-08-24T14:15:22Z", 
      "cryptoCurrency": "string", 
      "executionPlanNo": "string", 
      "fiatCurrency": "string", 
      "obtainAmount": "string", 
      "orderId": "string", 
      "price": "string", 
      "sourceAmount": "string", 
      "status": "CANCELLED", 
      "totalFee": "string" 
    } 
  ], 
  "message": "string", 
  "success": true 
} 
 
CommonRet«List«Recurring Buy Order Payments»»
42.641. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
[Recurring_Buy_Order_Payments]
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_List_ToCoinList_
{ 
  "code": "string", 
  "data": [ 
    { 
      "coin": "string", 
      "fromMax": 0, 
      "fromMin": 0 
    } 
  ], 
  "message": "string", 
  "success": true 
} 
 
CommonRet«List«ToCoinList»»
42.642. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
[ToCoinList]
false
none
返回的具体数据信息
message
string
false
none
消息内容


---

## Page 349

sapi-v7.4.md
2024-05-08
349 / 419
Name
Type
Required
Restrictions
Description
success
boolean
false
none
none
CommonRet_List_taker_commission_rate_
{ 
  "code": "string", 
  "data": [ 
    { 
      "baseCommissionRate": 0, 
      "commissionRate": 0, 
      "tradeMethodIdentifier": "string", 
      "tradeType": "string" 
    } 
  ], 
  "message": "string", 
  "success": true 
} 
 
CommonRet«List«taker commission rate»»
42.643. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
[taker_commission_rate]
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_List_
{ 
  "code": "string", 
  "data": [ 
    {} 
  ], 
  "message": "string", 
  "success": true 
} 
 
CommonRet«List»
42.644. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
[object]
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_MakeOrderResp_
{ 
  "code": "string", 
  "data": { 
    "orderMatch": { 
      "additionalKycVerify": 0, 
      "address": "string", 
      "advMainUserId": 0, 
      "advMakerRoles": "string", 
      "advOrderId": 0, 
      "advOrderNumber": "string", 
      "advUserId": 0, 
      "allowComplainTime": "2019-08-24T14:15:22Z", 


---

## Page 350

sapi-v7.4.md
2024-05-08
350 / 419
      "amount": 0, 
      "asset": "string", 
      "assetTicketSize": "string", 
      "buyerCompanyAccountName": "string", 
      "buyerCreditScore": 0, 
      "buyerMobilePhone": "string", 
      "buyerName": "string", 
      "buyerNickname": "string", 
      "canCancelComplaintOrder": true, 
      "cancelComplaintTime": "2019-08-24T14:15:22Z", 
      "cancelReasonAdditional": "string", 
      "cancelReasonDesc": "string", 
      "cancelTime": "2019-08-24T14:15:22Z", 
      "chatUnreadCount": 0, 
      "classify": "string", 
      "clientType": "string", 
      "commission": 0, 
      "commissionRate": 0, 
      "complainFreezeTime": "2019-08-24T14:15:22Z", 
      "complaintDeadline": "2019-08-24T14:15:22Z", 
      "complaintReason": "string", 
      "complaintStatus": 0, 
      "confirmPaidType": "string", 
      "confirmPayEndTime": "2019-08-24T14:15:22Z", 
      "confirmPayTime": "2019-08-24T14:15:22Z", 
      "confirmPayTimeout": 0, 
      "confirmPayedExpireMinute": 0, 
      "createTime": "2019-08-24T14:15:22Z", 
      "currencyRate": 0, 
      "currencyTicketSize": "string", 
      "fiatSymbol": "string", 
      "fiatUnit": "string", 
      "idNumber": "string", 
      "isBuyerCompanyAccount": true, 
      "isChatEnabled": true, 
      "isComplaintAllowed": true, 
      "isRiskCount": 0, 
      "isSellerCompanyAccount": true, 
      "isSupportVirtualNum": true, 
      "lengthOfConfirmTime": 0, 
      "lengthOfPayTime": 0, 
      "mainUserId": 0, 
      "maker": { 
        "advConfirmTime": 0, 
        "badges": [ 
          "string" 
        ], 
        "businessMobile": "string", 
        "businessStatus": 0, 
        "complaintCount": 0, 
        "countyCode": "string", 
        "createTime": "2019-08-24T14:15:22Z", 
        "email": "string", 
        "eqMargin": 0, 
        "eqMarginUnit": "string", 
        "fiatTradingAccount": 0, 
        "firstOrderDays": 0, 
        "fundpwdStatus": 0, 
        "id": 0, 
        "informMethods": "string", 
        "maliceInitiatorCount": 0, 
        "margin": 0, 
        "marginAsset": { 
          "asset": null, 
          "createTime": null, 
          "decimalScale": null, 
          "iconUrl": null, 
          "isEnable": null, 
          "isTransVisible": null, 
          "name": null, 
          "ranking": null, 
          "updateTime": null 
        }, 
        "marginFreeze": 0, 
        "marginStatsItems": [ 
          {} 
        ], 
        "marginUnit": "string", 
        "maskedBusinessMobile": "string", 
        "maskedEmail": "string", 
        "merchantType": "string", 


---

## Page 351

sapi-v7.4.md
2024-05-08
351 / 419
        "mobile": "string", 
        "mobileDisplayStatus": 0, 
        "monthFinishRate": 0, 
        "monthOrderCount": 0, 
        "nickColor": "string", 
        "nickName": "string", 
        "onlineStatus": 0, 
        "orderCount": 0, 
        "overComplained": 0, 
        "parentId": 0, 
        "payMethodCount": 0, 
        "proMerchantVo": { 
          "merchantDescription": null, 
          "merchantLogo": null 
        }, 
        "realName": "string", 
        "registerDays": 0, 
        "registrationTime": "2019-08-24T14:15:22Z", 
        "tradingAccount": 0, 
        "updateTime": "2019-08-24T14:15:22Z", 
        "userGradeInstanceVo": { 
          "agreementSigned": null, 
          "authorityId": null, 
          "createTime": null, 
          "emailStatus": null, 
          "id": null, 
          "kycStatus": null, 
          "marginStatus": null, 
          "mobileStatus": null, 
          "nickNameStatus": null, 
          "parentId": null, 
          "qualificationId": null, 
          "updateTime": null, 
          "userGradeQualificationVo": null, 
          "userId": null 
        }, 
        "userId": 0, 
        "userKycVo": { 
          "address": null, 
          "addressStatus": null, 
          "basicStatus": null, 
          "certificateStatus": null, 
          "companyName": null, 
          "countyCode": null, 
          "createTime": null, 
          "faceStatus": null, 
          "firstName": null, 
          "idNo": null, 
          "identityStatus": null, 
          "kycLevel": null, 
          "kycStatus": null, 
          "kycType": null, 
          "lastName": null, 
          "middleName": null, 
          "updateTime": null, 
          "userId": null 
        }, 
        "userNo": "string", 
        "userOrderHistoryStatsVo": { 
          "accountAge": null, 
          "appealedOrderCountHistorical": null, 
          "appealedOrderCountLast30Days": null, 
          "appealedRateHistorical": null, 
          "appealedRateLast30Days": null, 
          "avgPayTime": null, 
          "avgPayTimeOfLatest30day": null, 
          "avgReleaseTime": null, 
          "avgReleaseTimeOfLatest30day": null, 
          "buyOrderNum": null, 
          "buyOrderNumOfLatest30day": null, 
          "canceledBuyOrderNum": null, 
          "canceledBuyOrderNumOfLatest30day": null, 
          "completedBuyOrderNum": null, 
          "completedBuyOrderNumOfLatest30day": null, 
          "completedBuyOrderTotalBtcAmount": null, 
          "completedBuyOrderTotalBtcAmountOfLatest30day": null, 
          "completedOrderNum": null, 
          "completedOrderNumOfLatest30day": null, 
          "completedOrderTotalBtcAmount": null, 
          "completedOrderTotalBtcAmountOfLatest30day": null, 
          "completedSellOrderNum": null, 


---

## Page 352

sapi-v7.4.md
2024-05-08
352 / 419
          "completedSellOrderNumOfLatest30day": null, 
          "completedSellOrderTotalBtcAmount": null, 
          "completedSellOrderTotalBtcAmountOfLatest30day": null, 
          "counterpartyNum": null, 
          "creditScore": null, 
          "finishRate": null, 
          "finishRateLatest30Day": null 
        }, 
        "userOrderInProgressStatsVo": { 
          "buyerPayedCount": null, 
          "inAppealCount": null, 
          "inAppealCountAfterBuyerPaid": null, 
          "inAppealCountAfterCancelled": null, 
          "inAppealCountAfterCancelledBySystem": null, 
          "inAppealCountAfterCompleted": null, 
          "inProcessCount": null, 
          "tradingCount": null, 
          "userId": null 
        }, 
        "userType": "string" 
      }, 
      "merchantNo": "string", 
      "nickColor": "string", 
      "notifyPayEndTime": "2019-08-24T14:15:22Z", 
      "notifyPayTime": "2019-08-24T14:15:22Z", 
      "notifyPayedExpireMinute": 0, 
      "onlineStatus": "string", 
      "orderComplaintAmount": { 
        "complaintAmount": 0, 
        "completedComplaintAmount": 0, 
        "processingComplaintAmount": 0 
      }, 
      "orderNumber": "string", 
      "orderStatus": 0, 
      "orderTakerRoles": "string", 
      "origin": "string", 
      "payAccount": "string", 
      "payBank": "string", 
      "payMethods": [ 
        { 
          "advCount": 0, 
          "createTime": "2019-08-24T14:15:22Z", 
          "currentPayAmount": 0, 
          "fieldList": [ 
            null 
          ], 
          "iconUrlColor": "string", 
          "id": 0, 
          "isRemoved": 0, 
          "mainUserId": 0, 
          "online": true, 
          "payLimit": 0, 
          "payLimitUnit": "string", 
          "payStatus": "[", 
          "tradeMethodBgColor": "string", 
          "tradeMethodIdentifier": "string", 
          "tradeMethodName": "string", 
          "tradeMethodRisk": "string", 
          "tradeMethodShortName": "string", 
          "updateTime": "2019-08-24T14:15:22Z", 
          "userId": 0 
        } 
      ], 
      "paySubBank": "string", 
      "payTimeLimit": 0, 
      "payType": "string", 
      "payTypeDesc": "string", 
      "payee": "string", 
      "price": 0, 
      "priceTicketSize": "string", 
      "publisherType": "string", 
      "qrCodePath": "string", 
      "quickConfirmAmountUpLimit": 0, 
      "remark": "string", 
      "selectedPayId": 0, 
      "sellerCompanyAccountName": "string", 
      "sellerCreditScore": 0, 
      "sellerMobilePhone": "string", 
      "sellerName": "string", 
      "sellerNickname": "string", 
      "statFlag": 0, 


---

## Page 353

sapi-v7.4.md
2024-05-08
353 / 419
      "store": { 
        "applyStatus": 0, 
        "availableMargin": 0, 
        "countryCode": "string", 
        "distance": 0, 
        "enable": "string", 
        "fineAmount": 0, 
        "friOpenTime": "string", 
        "friOpenTimeLocal": "string", 
        "fullAddress": "string", 
        "geoCode": "string", 
        "latitude": 0, 
        "longitude": 0, 
        "margin": 0, 
        "marginFreeze": 0, 
        "marginUnit": "string", 
        "monOpenTime": "string", 
        "monOpenTimeLocal": "string", 
        "processingAmount": 0, 
        "refundProcessingAmount": 0, 
        "refundableFineAmount": 0, 
        "remark": "string", 
        "satOpenTime": "string", 
        "satOpenTimeLocal": "string", 
        "status": 0, 
        "storeAddressVo": { 
          "building": null, 
          "city": null, 
          "country": null, 
          "flat": null, 
          "floor": null, 
          "province": null, 
          "remark": null, 
          "street": null, 
          "zipCode": null 
        }, 
        "storeId": 0, 
        "storeMaterialItemVoList": [ 
          {} 
        ], 
        "storeName": "string", 
        "storeShortName": "string", 
        "submissionTime": "2019-08-24T14:15:22Z", 
        "sunOpenTime": "string", 
        "sunOpenTimeLocal": "string", 
        "thuOpenTime": "string", 
        "thuOpenTimeLocal": "string", 
        "timeZone": "string", 
        "tueOpenTime": "string", 
        "tueOpenTimeLocal": "string", 
        "updateTime": "2019-08-24T14:15:22Z", 
        "userId": 0, 
        "valid": true, 
        "wedOpenTime": "string", 
        "wedOpenTimeLocal": "string" 
      }, 
      "sysCancelTime": "2019-08-24T14:15:22Z", 
      "taker": { 
        "advConfirmTime": 0, 
        "badges": [ 
          "string" 
        ], 
        "businessMobile": "string", 
        "businessStatus": 0, 
        "complaintCount": 0, 
        "countyCode": "string", 
        "createTime": "2019-08-24T14:15:22Z", 
        "email": "string", 
        "eqMargin": 0, 
        "eqMarginUnit": "string", 
        "fiatTradingAccount": 0, 
        "firstOrderDays": 0, 
        "fundpwdStatus": 0, 
        "id": 0, 
        "informMethods": "string", 
        "maliceInitiatorCount": 0, 
        "margin": 0, 
        "marginAsset": { 
          "asset": null, 
          "createTime": null, 
          "decimalScale": null, 


---

## Page 354

sapi-v7.4.md
2024-05-08
354 / 419
          "iconUrl": null, 
          "isEnable": null, 
          "isTransVisible": null, 
          "name": null, 
          "ranking": null, 
          "updateTime": null 
        }, 
        "marginFreeze": 0, 
        "marginStatsItems": [ 
          {} 
        ], 
        "marginUnit": "string", 
        "maskedBusinessMobile": "string", 
        "maskedEmail": "string", 
        "merchantType": "string", 
        "mobile": "string", 
        "mobileDisplayStatus": 0, 
        "monthFinishRate": 0, 
        "monthOrderCount": 0, 
        "nickColor": "string", 
        "nickName": "string", 
        "onlineStatus": 0, 
        "orderCount": 0, 
        "overComplained": 0, 
        "parentId": 0, 
        "payMethodCount": 0, 
        "proMerchantVo": { 
          "merchantDescription": null, 
          "merchantLogo": null 
        }, 
        "realName": "string", 
        "registerDays": 0, 
        "registrationTime": "2019-08-24T14:15:22Z", 
        "tradingAccount": 0, 
        "updateTime": "2019-08-24T14:15:22Z", 
        "userGradeInstanceVo": { 
          "agreementSigned": null, 
          "authorityId": null, 
          "createTime": null, 
          "emailStatus": null, 
          "id": null, 
          "kycStatus": null, 
          "marginStatus": null, 
          "mobileStatus": null, 
          "nickNameStatus": null, 
          "parentId": null, 
          "qualificationId": null, 
          "updateTime": null, 
          "userGradeQualificationVo": null, 
          "userId": null 
        }, 
        "userId": 0, 
        "userKycVo": { 
          "address": null, 
          "addressStatus": null, 
          "basicStatus": null, 
          "certificateStatus": null, 
          "companyName": null, 
          "countyCode": null, 
          "createTime": null, 
          "faceStatus": null, 
          "firstName": null, 
          "idNo": null, 
          "identityStatus": null, 
          "kycLevel": null, 
          "kycStatus": null, 
          "kycType": null, 
          "lastName": null, 
          "middleName": null, 
          "updateTime": null, 
          "userId": null 
        }, 
        "userNo": "string", 
        "userOrderHistoryStatsVo": { 
          "accountAge": null, 
          "appealedOrderCountHistorical": null, 
          "appealedOrderCountLast30Days": null, 
          "appealedRateHistorical": null, 
          "appealedRateLast30Days": null, 
          "avgPayTime": null, 
          "avgPayTimeOfLatest30day": null, 


---

## Page 355

sapi-v7.4.md
2024-05-08
355 / 419
          "avgReleaseTime": null, 
          "avgReleaseTimeOfLatest30day": null, 
          "buyOrderNum": null, 
          "buyOrderNumOfLatest30day": null, 
          "canceledBuyOrderNum": null, 
          "canceledBuyOrderNumOfLatest30day": null, 
          "completedBuyOrderNum": null, 
          "completedBuyOrderNumOfLatest30day": null, 
          "completedBuyOrderTotalBtcAmount": null, 
          "completedBuyOrderTotalBtcAmountOfLatest30day": null, 
          "completedOrderNum": null, 
          "completedOrderNumOfLatest30day": null, 
          "completedOrderTotalBtcAmount": null, 
          "completedOrderTotalBtcAmountOfLatest30day": null, 
          "completedSellOrderNum": null, 
          "completedSellOrderNumOfLatest30day": null, 
          "completedSellOrderTotalBtcAmount": null, 
          "completedSellOrderTotalBtcAmountOfLatest30day": null, 
          "counterpartyNum": null, 
          "creditScore": null, 
          "finishRate": null, 
          "finishRateLatest30Day": null 
        }, 
        "userOrderInProgressStatsVo": { 
          "buyerPayedCount": null, 
          "inAppealCount": null, 
          "inAppealCountAfterBuyerPaid": null, 
          "inAppealCountAfterCancelled": null, 
          "inAppealCountAfterCancelledBySystem": null, 
          "inAppealCountAfterCompleted": null, 
          "inProcessCount": null, 
          "tradingCount": null, 
          "userId": null 
        }, 
        "userType": "string" 
      }, 
      "takerAmount": 0, 
      "takerCommission": 0, 
      "takerCommissionRate": 0, 
      "totalPrice": 0, 
      "tradeMethodCommissionRateVoList": [ 
        { 
          "commissionRate": 0, 
          "tradeMethodIdentifier": "string", 
          "tradeMethodName": "string" 
        } 
      ], 
      "tradeType": "BUY", 
      "unreadCount": 0, 
      "updateTime": "2019-08-24T14:15:22Z", 
      "userId": 0 
    }, 
    "result": true 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«MakeOrderResp»
42.645. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
MakeOrderResp
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_MarkOrderAsPaidResp_
{ 
  "code": "string", 
  "data": { 
    "complainFreezeTime": "2019-08-24T14:15:22Z", 


---

## Page 356

sapi-v7.4.md
2024-05-08
356 / 419
    "confirmPayEndTime": "2019-08-24T14:15:22Z", 
    "notifyPayTime": "2019-08-24T14:15:22Z", 
    "orderNumber": "string", 
    "orderStatus": 0, 
    "selectedPayId": 0 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«MarkOrderAsPaidResp»
42.646. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
MarkOrderAsPaidResp
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_Merchant_Start_Rest_Response_
{ 
  "code": "string", 
  "data": { 
    "suspendEndTime": "2019-08-24T14:15:22Z" 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«Merchant Start Rest Response»
42.647. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
Merchant_Start_Rest_Response
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_MerchantAdsDetailResp_
{ 
  "code": "string", 
  "data": { 
    "buyList": [ 
      { 
        "adVisibleRet": { 
          "freeAmountVisible": 0, 
          "orderFlowVisible": 0, 
          "surplusAmountVisible": 0, 
          "userSetVisible": 0 
        }, 
        "advNo": "string", 
        "asset": "string", 
        "assetScale": 0, 
        "assetTicketSize": "string", 
        "autoReply": "string", 
        "buyerBtcAmount": 0, 
        "buyerRegisterLimit": 0, 
        "currencyTicketSize": "string", 
        "dynamicMaxOrderAmount": 0, 
        "dynamicMaxOrderPrice": 0, 
        "fiatScale": 0, 
        "fiatSymbol": "string", 
        "fiatUnit": "string", 


---

## Page 357

sapi-v7.4.md
2024-05-08
357 / 419
        "isConformed": true, 
        "kycLimit": 0, 
        "logo": "string", 
        "mainUserId": 0, 
        "maxOrderAmount": 0, 
        "maxOrderPrice": 0, 
        "minOrderAmount": 0, 
        "minOrderPrice": 0, 
        "offlineReason": "string", 
        "payMethodDtos": [ 
          { 
            "iconUrlColor": null, 
            "id": null, 
            "identifier": null, 
            "payAccount": null, 
            "payBank": null, 
            "payMethodId": null, 
            "paySubBank": null, 
            "payType": null, 
            "tradeMethodBgColor": null, 
            "tradeMethodName": null, 
            "tradeMethodShortName": null 
          } 
        ], 
        "payTimeLimit": 0, 
        "payTypeList": [ 
          "string" 
        ], 
        "price": 0, 
        "priceScale": 0, 
        "priceTicketSize": "string", 
        "remark": "string", 
        "surplusAmount": 0, 
        "takerAdditionalKycRequired": 0, 
        "tradeType": "BUY", 
        "userId": 0 
      } 
    ], 
    "merchant": { 
      "advConfirmTime": 0, 
      "assetTicketSize": "string", 
      "authentication": true, 
      "bindMobile": true, 
      "chanelInvolved": "string", 
      "emailVerified": true, 
      "firstOrderDays": 0, 
      "idVerified": true, 
      "margin": 0, 
      "marginUnit": "string", 
      "merchantNo": "string", 
      "monthFinishRate": 0, 
      "monthOrderCount": 0, 
      "nickColor": "string", 
      "nickName": "string", 
      "onlineStatus": "string", 
      "orderCount": 0, 
      "registerDays": 0, 
      "userGradeInstanceResp": { 
        "agreementSigned": 0, 
        "emailStatus": 0, 
        "kycStatus": 0, 
        "marginStatus": 0, 
        "mobileStatus": 0, 
        "nickNameStatus": 0, 
        "userGrade": 0 
      }, 
      "userKycResp": { 
        "addressStatus": "string", 
        "kycType": "string" 
      }, 
      "userNo": "string", 
      "userStatsResp": { 
        "avgPayTimeOfLatest30day": 0, 
        "avgReleaseTimeOfLatest30day": 0, 
        "completedBuyOrderNum": 0, 
        "completedBuyOrderNumOfLatest30day": 0, 
        "completedBuyOrderTotalBtcAmount": 0, 
        "completedOrderNum": 0, 
        "completedOrderNumOfLatest30day": 0, 
        "completedOrderTotalBtcAmount": 0, 
        "completedOrderTotalBtcAmountOfLatest30day": 0, 


---

## Page 358

sapi-v7.4.md
2024-05-08
358 / 419
        "completedSellOrderNum": 0, 
        "completedSellOrderNumOfLatest30day": 0, 
        "completedSellOrderTotalBtcAmount": 0, 
        "finishRateLatest30day": 0, 
        "firstOrderDays": 0, 
        "payMethodCount": 0, 
        "registerDays": 0 
      }, 
      "userType": "string" 
    }, 
    "sellList": [ 
      { 
        "adVisibleRet": { 
          "freeAmountVisible": 0, 
          "orderFlowVisible": 0, 
          "surplusAmountVisible": 0, 
          "userSetVisible": 0 
        }, 
        "advNo": "string", 
        "asset": "string", 
        "assetScale": 0, 
        "assetTicketSize": "string", 
        "autoReply": "string", 
        "buyerBtcAmount": 0, 
        "buyerRegisterLimit": 0, 
        "currencyTicketSize": "string", 
        "dynamicMaxOrderAmount": 0, 
        "dynamicMaxOrderPrice": 0, 
        "fiatScale": 0, 
        "fiatSymbol": "string", 
        "fiatUnit": "string", 
        "isConformed": true, 
        "kycLimit": 0, 
        "logo": "string", 
        "mainUserId": 0, 
        "maxOrderAmount": 0, 
        "maxOrderPrice": 0, 
        "minOrderAmount": 0, 
        "minOrderPrice": 0, 
        "offlineReason": "string", 
        "payMethodDtos": [ 
          { 
            "iconUrlColor": null, 
            "id": null, 
            "identifier": null, 
            "payAccount": null, 
            "payBank": null, 
            "payMethodId": null, 
            "paySubBank": null, 
            "payType": null, 
            "tradeMethodBgColor": null, 
            "tradeMethodName": null, 
            "tradeMethodShortName": null 
          } 
        ], 
        "payTimeLimit": 0, 
        "payTypeList": [ 
          "string" 
        ], 
        "price": 0, 
        "priceScale": 0, 
        "priceTicketSize": "string", 
        "remark": "string", 
        "surplusAmount": 0, 
        "takerAdditionalKycRequired": 0, 
        "tradeType": "BUY", 
        "userId": 0 
      } 
    ] 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«MerchantAdsDetailResp»
42.648. Properties


---

## Page 359

sapi-v7.4.md
2024-05-08
359 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
MerchantAdsDetailResp
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_OcbsRet_
{ 
  "code": "string", 
  "data": { 
    "amount": 0, 
    "externalId": "string", 
    "msg": "string", 
    "objs": [ 
      {} 
    ], 
    "rows": {} 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«OcbsRet»
42.649. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
OcbsRet
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_OrderAdditionalKycVerifyResp_
{ 
  "code": "string", 
  "data": { 
    "kycVerified": true, 
    "orderNumber": "string" 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«OrderAdditionalKycVerifyResp»
42.650. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
OrderAdditionalKycVerifyResp
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_OrderMatchResp_
{ 
  "code": "string", 
  "data": { 
    "additionalKycVerify": 0, 
    "address": "string", 


---

## Page 360

sapi-v7.4.md
2024-05-08
360 / 419
    "advOrderId": 0, 
    "advOrderNumber": "string", 
    "allowComplainTime": "2019-08-24T14:15:22Z", 
    "amount": 0, 
    "asset": "string", 
    "assetTicketSize": "string", 
    "authentication": true, 
    "avgPayPeriod": 0, 
    "avgReleasePeriod": 0, 
    "buyerMobilePhone": "string", 
    "buyerName": "string", 
    "buyerNickname": "string", 
    "canCancelComplaintOrder": true, 
    "cancelTime": "2019-08-24T14:15:22Z", 
    "clientType": "string", 
    "commission": 0, 
    "commissionRate": 0, 
    "complainFreezeTime": "2019-08-24T14:15:22Z", 
    "complaintDeadline": "2019-08-24T14:15:22Z", 
    "complaintReason": "string", 
    "complaintStatus": 0, 
    "confirmPayEndTime": "2019-08-24T14:15:22Z", 
    "confirmPayTime": "2019-08-24T14:15:22Z", 
    "confirmPayTimeout": 0, 
    "confirmPayedExpireMinute": 0, 
    "createTime": "2019-08-24T14:15:22Z", 
    "currencyRate": 0, 
    "currencyTicketSize": "string", 
    "expectedPayTime": "2019-08-24T14:15:22Z", 
    "expectedReleaseTime": "2019-08-24T14:15:22Z", 
    "fiatSymbol": "string", 
    "fiatUnit": "string", 
    "iconUrl": "string", 
    "idNumber": "string", 
    "isComplaintAllowed": true, 
    "merchantNo": "string", 
    "nickColor": "string", 
    "notifyPayEndTime": "2019-08-24T14:15:22Z", 
    "notifyPayTime": "2019-08-24T14:15:22Z", 
    "notifyPayedExpireMinute": 0, 
    "onlineStatus": "string", 
    "orderNumber": "string", 
    "orderStatus": 0, 
    "origin": "string", 
    "payAccount": "string", 
    "payBank": "string", 
    "payMethods": [ 
      { 
        "fields": [ 
          { 
            "fieldContentType": null, 
            "fieldId": null, 
            "fieldName": null, 
            "fieldValue": null, 
            "hintWord": null, 
            "isCopyable": null, 
            "isRequired": null, 
            "lengthLimit": null, 
            "restrictionType": null, 
            "sequence": null 
          } 
        ], 
        "iconUrlColor": "string", 
        "id": 0, 
        "identifier": "string", 
        "tradeMethodName": "string" 
      } 
    ], 
    "paySubBank": "string", 
    "payType": "string", 
    "payee": "string", 
    "price": 0, 
    "priceTicketSize": "string", 
    "qrCodePath": "string", 
    "remark": "string", 
    "selectedPayId": 0, 
    "sellerMobilePhone": "string", 
    "sellerName": "string", 
    "sellerNickname": "string", 
    "takerAmount": 0, 
    "takerCommission": 0, 


---

## Page 361

sapi-v7.4.md
2024-05-08
361 / 419
    "takerCommissionRate": 0, 
    "totalPrice": 0, 
    "tradeMethodCommissionRateVoList": [ 
      { 
        "commissionRate": 0, 
        "tradeMethodIdentifier": "string", 
        "tradeMethodName": "string" 
      } 
    ], 
    "tradeType": "BUY", 
    "unreadCount": 0, 
    "updateTime": "2019-08-24T14:15:22Z" 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«OrderMatchResp»
42.651. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
OrderMatchResp0
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_OrderMatchStatsResp_
{ 
  "code": "string", 
  "data": { 
    "buyerPayedCount": 0, 
    "inAppealCount": 0, 
    "inProcessCount": 0, 
    "tradingCount": 0 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«OrderMatchStatsResp»
42.652. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
OrderMatchStatsResp
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_PayMethodResp_
{ 
  "code": "string", 
  "data": { 
    "advCount": 0, 
    "createTime": "2019-08-24T14:15:22Z", 
    "currentPayAmount": 0, 
    "fieldList": [ 
      { 
        "createTime": "2019-08-24T14:15:22Z", 
        "errorKey": "string", 
        "errorWord": "string", 
        "fieldContentType": "string", 
        "fieldId": "string", 
        "fieldName": "string", 


---

## Page 362

sapi-v7.4.md
2024-05-08
362 / 419
        "fieldTitle": "string", 
        "fieldTitleKey": "string", 
        "fieldValue": "string", 
        "hintKey": "string", 
        "hintWord": "string", 
        "id": 0, 
        "isCopyable": 0, 
        "isDisplay": 0, 
        "isEncrypt": 0, 
        "isRequired": 0, 
        "lengthLimit": 0, 
        "restrictionType": 0, 
        "sequence": 0, 
        "status": 0, 
        "updateTime": "2019-08-24T14:15:22Z" 
      } 
    ], 
    "forbidReason": "string", 
    "id": 0, 
    "isRemoved": 0, 
    "mainUserId": 0, 
    "payAccount": "string", 
    "payBank": "string", 
    "payLimit": 0, 
    "payLimitUnit": "string", 
    "payStatus": "ACTIVE", 
    "paySubBank": "string", 
    "payType": "ALIPAY", 
    "payee": "string", 
    "qrCodePath": "string", 
    "tradeMethod": { 
      "bgColor": "string", 
      "chatNeed": 0, 
      "createTime": "2019-08-24T14:15:22Z", 
      "iconUrlColor": "string", 
      "iconUrlGray": "string", 
      "id": 0, 
      "identifier": "string", 
      "isOnline": 0, 
      "isRecommended": 0, 
      "isVisible": 0, 
      "multiAllow": 0, 
      "name": "string", 
      "nameKey": "string", 
      "remark": "string", 
      "risk": "string", 
      "riskKey": "string", 
      "riskLevel": 0, 
      "sequence": 0, 
      "shortName": "string", 
      "shortNameKey": "string", 
      "tradeMethodCode": 0, 
      "typeCode": "string", 
      "typeName": "string", 
      "updateTime": "2019-08-24T14:15:22Z" 
    }, 
    "tradeMethodIdentifier": "string", 
    "updateTime": "2019-08-24T14:15:22Z", 
    "userId": 0 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«PayMethodResp»
42.653. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
PayMethodResp
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_Redeem_a_code_response_information_


---

## Page 363

sapi-v7.4.md
2024-05-08
363 / 419
{ 
  "code": "string", 
  "data": { 
    "amount": 0, 
    "identityNo": "string", 
    "referenceNo": "string", 
    "token": "string" 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«Redeem a code response information»
42.654. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
Redeem_a_code_response_information
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_Reponse_to_identify_whether_the_binance_code_is_valid._
{ 
  "code": "string", 
  "data": { 
    "amount": 0, 
    "isCashPickup": true, 
    "minterInfo": { 
      "country": "string", 
      "dob": "string", 
      "fullName": "string", 
      "state": "string" 
    }, 
    "token": "string", 
    "valid": true 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«Reponse to identify whether the binance code is valid.»
42.655. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
Reponse_to_identify_whether_the_binance_code_is_valid.
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_Response_for_creating_a_code_
{ 
  "code": "string", 
  "data": { 
    "code": "string", 
    "expiredTime": "2019-08-24T14:15:22Z", 
    "referenceNo": "string" 
  }, 
  "message": "string", 
  "success": true 
} 
 


---

## Page 364

sapi-v7.4.md
2024-05-08
364 / 419
CommonRet«Response for creating a code »
42.656. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
Response_for_creating_a_code_
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_RiskWarningTipsResp_
{ 
  "code": "string", 
  "data": { 
    "riskHints": [ 
      { 
        "riskTips": "string", 
        "riskType": "string" 
      } 
    ] 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«RiskWarningTipsResp»
42.657. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
RiskWarningTipsResp
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_SearchResult_ThirdPartyNftAssetVo_
{ 
  "code": "string", 
  "data": { 
    "rows": [ 
      { 
        "assetStatus": "string", 
        "assetType": "string", 
        "brandingId": 0, 
        "brandingName": "string", 
        "buyOutPrice": 0, 
        "collectionId": 0, 
        "collectionName": "string", 
        "contractAddress": "string", 
        "creatorName": "string", 
        "currency": "string", 
        "expireDate": 0, 
        "itemTypeId": 0, 
        "itemTypeName": "string", 
        "listingOrderNumber": 0, 
        "nftInfoId": 0, 
        "orderType": "string", 
        "ownerName": "string", 
        "productId": 0, 
        "rarity": "string", 
        "startingPrice": 0, 
        "tokenId": "string" 
      } 
    ], 
    "total": 0 
  }, 


---

## Page 365

sapi-v7.4.md
2024-05-08
365 / 419
  "message": "string", 
  "params": [ 
    {} 
  ], 
  "success": true 
} 
 
CommonRet«SearchResult«ThirdPartyNftAssetVo»»
42.658. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
SearchResult_ThirdPartyNftAssetVo_
false
none
返回的具体数据信息
message
string
false
none
消息内容
params
[object]
false
none
异常参数，通常⽤于错误信息参数占位符替换
success
boolean
false
none
none
CommonRet_UserAdsCategoryResp_
{ 
  "code": "string", 
  "data": { 
    "advClassifies": [ 
      "string" 
    ] 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«UserAdsCategoryResp»
42.659. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
UserAdsCategoryResp
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_UserOrderHistoryStatsResp_
{ 
  "code": "string", 
  "data": { 
    "completedOrderNum": 0, 
    "completedOrderNumOfLatest30day": 0, 
    "finishRate": 0, 
    "finishRateLatest30Day": 0, 
    "numberOfTradesWithCounterpartyCompleted30day": 0, 
    "registerDays": 0 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«UserOrderHistoryStatsResp»
42.660. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功


---

## Page 366

sapi-v7.4.md
2024-05-08
366 / 419
Name
Type
Required
Restrictions
Description
data
UserOrderHistoryStatsResp
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_Void_
{ 
  "code": "string", 
  "message": "string", 
  "success": true 
} 
 
CommonRet«Void»
42.661. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_boolean_
{ 
  "code": "string", 
  "data": true, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«boolean»
42.662. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
boolean
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_commission_rate_overview_
{ 
  "code": "string", 
  "data": { 
    "assetRetList": [ 
      { 
        "asset": "string", 
        "assetLogoUrl": "string", 
        "assetName": "string", 
        "items": [ 
          { 
            "area": null, 
            "channel": null, 
            "fiat": null, 
            "makerBuyBaseCommissionRate": null, 
            "makerBuyCommissionRate": null, 
            "makerSellBaseCommissionRate": null, 
            "makerSellCommissionRate": null, 
            "takerBuyBaseCommissionRate": null, 
            "takerBuyCommissionRate": null, 
            "takerSellBaseCommissionRate": null, 


---

## Page 367

sapi-v7.4.md
2024-05-08
367 / 419
            "takerSellCommissionRate": null 
          } 
        ] 
      } 
    ], 
    "userDiscountOffRateMaker": 0, 
    "userDiscountOffRateTaker": 0, 
    "userLevel": 0 
  }, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«commission rate overview»
42.663. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
commission_rate_overview
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_object_
{ 
  "code": "string", 
  "data": {}, 
  "message": "string", 
  "success": true 
} 
 
CommonRet«object»
42.664. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
object
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none
CommonRet_string_
{ 
  "code": "string", 
  "data": "string", 
  "message": "string", 
  "success": true 
} 
 
CommonRet«string»
42.665. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
错误码，000000表示成功
data
string
false
none
返回的具体数据信息
message
string
false
none
消息内容
success
boolean
false
none
none


---

## Page 368

sapi-v7.4.md
2024-05-08
368 / 419
DepositInquiryPageResponse_DepositInquiryDetailVo_
{ 
  "hasMore": true, 
  "list": [ 
    { 
      "address": "string", 
      "amount": 0, 
      "coin": "string", 
      "completedTime": "2019-08-24T14:15:22Z", 
      "expectedAmount": 0, 
      "feeAmount": 0, 
      "feeDeducted": true, 
      "feeFreezeStatus": 0, 
      "feeRatio": 0, 
      "feeShowed": true, 
      "feeUnit": "string", 
      "heightWarn": 0, 
      "insertTime": "2019-08-24T14:15:22Z", 
      "isCoinOnline": true, 
      "manualReviewTime": "2019-08-24T14:15:22Z", 
      "materialUploadTime": "2019-08-24T14:15:22Z", 
      "materials": [ 
        { 
          "id": 0, 
          "insertTime": "2019-08-24T14:15:22Z", 
          "materialKey": "string", 
          "name": "string", 
          "requestId": "string" 
        } 
      ], 
      "needDays": 0, 
      "network": "string", 
      "noEnoughBalance": true, 
      "platformName": "string", 
      "reason": "string", 
      "reasonKey": "string", 
      "refundAddress": "string", 
      "refundAddressTag": "string", 
      "refundAmount": 0, 
      "refundCoin": "string", 
      "remark": "string", 
      "requestId": "string", 
      "requestType": 0, 
      "selfReturnStatus": 0, 
      "sourceAddress": "string", 
      "status": 0, 
      "supplementTypes": [ 
        "string" 
      ], 
      "transactionId": "string", 
      "txId": "string", 
      "type": 0, 
      "updateTime": "2019-08-24T14:15:22Z", 
      "userId": 0, 
      "workOrder": "string" 
    } 
  ], 
  "page": 0, 
  "size": 0, 
  "total": 0 
} 
 
DepositInquiryPageResponse«DepositInquiryDetailVo»
42.666. Properties
Name
Type
Required
Restrictions
Description
hasMore
boolean
false
none
none
list
[DepositInquiryDetailVo]
false
none
none
page
integer(int32)
false
none
none
size
integer(int32)
false
none
none
total
integer(int32)
false
none
none


---

## Page 369

sapi-v7.4.md
2024-05-08
369 / 419
Fiat_detail
{ 
  "countryCode": "string", 
  "currencyCode": "string", 
  "currencyScale": 0, 
  "currencySymbol": "string", 
  "iconUrl": "string", 
  "priceScale": 0 
} 
 
Fiat detail
42.667. Properties
Name
Type
Required
Restrictions
Description
countryCode
string
false
none
Country code
currencyCode
string
false
none
Fiat currency code, e.g.: CNY
currencyScale
integer(int32)
false
none
Decimal precision scale
currencySymbol
string
false
none
Fiat currency symbol, e.g.: ¥
iconUrl
string
false
none
Fiat currency icon URL
priceScale
integer(int32)
false
none
Asset price decimal precision scale
FutureHisRes_SelectBrokerFutureTransferRes_
{ 
  "futuresType": 0, 
  "success": true, 
  "transfers": [ 
    { 
      "asset": "string", 
      "clientTranId": "string", 
      "from": "string", 
      "qty": "string", 
      "time": 0, 
      "to": "string", 
      "tranId": "string" 
    } 
  ] 
} 
 
FutureHisRes«SelectBrokerFutureTransferRes»
42.668. Properties
Name
Type
Required
Restrictions
Description
futuresType
integer(int32)
false
none
none
success
boolean
false
none
none
transfers
[SelectBrokerFutureTransferRes]
false
none
none
FutureHisRes_SelectSubAccountFutureTransferRes_
{ 
  "futuresType": 0, 
  "success": true, 
  "transfers": [ 
    { 
      "asset": "string", 
      "from": "string", 
      "qty": "string", 
      "time": 0, 
      "to": "string", 
      "tranId": 0 
    } 
  ] 


---

## Page 370

sapi-v7.4.md
2024-05-08
370 / 419
} 
 
FutureHisRes«SelectSubAccountFutureTransferRes»
42.669. Properties
Name
Type
Required
Restrictions
Description
futuresType
integer(int32)
false
none
none
success
boolean
false
none
none
transfers
[SelectSubAccountFutureTransferRes]
false
none
none
Margin_Statistic_Item
{ 
  "margin": 0, 
  "marginUnit": "string" 
} 
 
Margin Statistic Item
42.670. Properties
Name
Type
Required
Restrictions
Description
margin
number
false
none
Margin Item
marginUnit
string
false
none
Margin Symbol Item, e.g. USDT, BNB
Merchant_Start_Rest_Response
{ 
  "suspendEndTime": "2019-08-24T14:15:22Z" 
} 
 
Merchant Start Rest Response
42.671. Properties
Name
Type
Required
Restrictions
Description
suspendEndTime
string(date-time)
false
none
Suspend End Time
Page_VIP_Portal_Report_Config_Model_
{ 
  "current": 0, 
  "hitCount": true, 
  "optimizeCountSql": true, 
  "orders": [ 
    { 
      "asc": true, 
      "column": "string" 
    } 
  ], 
  "pages": 0, 
  "records": [ 
    { 
      "businessType": "string", 
      "fileTypes": [ 
        "string" 
      ], 
      "reportFields": [ 
        "string" 
      ], 
      "reportType": "string" 
    } 
  ], 


---

## Page 371

sapi-v7.4.md
2024-05-08
371 / 419
  "searchCount": true, 
  "size": 0, 
  "total": 0 
} 
 
Page«VIP Portal Report Config Model»
42.672. Properties
Name
Type
Required
Restrictions
Description
current
integer(int64)
false
none
none
hitCount
boolean
false
none
none
optimizeCountSql
boolean
false
none
none
orders
[OrderItem]
false
none
none
pages
integer(int64)
false
none
none
records
[VIP_Portal_Report_Config_Model]
false
none
none
searchCount
boolean
false
none
none
size
integer(int64)
false
none
none
total
integer(int64)
false
none
none
Page_VIP_Portal_Report_Item_Model_
{ 
  "current": 0, 
  "hitCount": true, 
  "optimizeCountSql": true, 
  "orders": [ 
    { 
      "asc": true, 
      "column": "string" 
    } 
  ], 
  "pages": 0, 
  "records": [ 
    { 
      "businessType": "string", 
      "createByUid": "string", 
      "dbCreateTime": "2019-08-24T14:15:22Z", 
      "dbModifyTime": "2019-08-24T14:15:22Z", 
      "emails": [ 
        "string" 
      ], 
      "endDate": "string", 
      "fileType": "string", 
      "pdfLink": "string", 
      "reportName": "string", 
      "reportType": "string", 
      "reportUrl": "string", 
      "s3Link": "string", 
      "source": "string", 
      "startDate": "string", 
      "status": 0, 
      "timezone": "string", 
      "url": "string", 
      "userId": "string" 
    } 
  ], 
  "searchCount": true, 
  "size": 0, 
  "total": 0 
} 
 
Page«VIP Portal Report Item Model»
42.673. Properties
Name
Type
Required
Restrictions
Description


---

## Page 372

sapi-v7.4.md
2024-05-08
372 / 419
Name
Type
Required
Restrictions
Description
current
integer(int64)
false
none
none
hitCount
boolean
false
none
none
optimizeCountSql
boolean
false
none
none
orders
[OrderItem]
false
none
none
pages
integer(int64)
false
none
none
records
[VIP_Portal_Report_Item_Model]
false
none
none
searchCount
boolean
false
none
none
size
integer(int64)
false
none
none
total
integer(int64)
false
none
none
Recurring_Buy_Order_Payments
{ 
  "contractNo": "string", 
  "contractSerialNo": "string", 
  "createTime": "2019-08-24T14:15:22Z", 
  "cryptoCurrency": "string", 
  "executionPlanNo": "string", 
  "fiatCurrency": "string", 
  "obtainAmount": "string", 
  "orderId": "string", 
  "price": "string", 
  "sourceAmount": "string", 
  "status": "CANCELLED", 
  "totalFee": "string" 
} 
 
Recurring Buy Order Payments
42.674. Properties
Name
Type
Required
Restrictions
Description
contractNo
string
false
none
contractNo
contractSerialNo
string
false
none
contractSerialNo
createTime
string(date-time)
false
none
订单创建时间
cryptoCurrency
string
false
none
虚拟币token
executionPlanNo
string
false
none
executionPlanNo
fiatCurrency
string
false
none
法币token
obtainAmount
string
false
none
虚拟币交易⾦额
orderId
string
false
none
订单号
price
string
false
none
价格
sourceAmount
string
false
none
法币交易⾦额
status
string
false
none
执⾏状态
totalFee
string
false
none
总⼿续费
42.674.1. Enumerated Values
Property
Value
status
CANCELLED
status
COMPLETED
status
FAILED
status
INITIAL
status
PROCESSING
status
SCHEDULED


---

## Page 373

sapi-v7.4.md
2024-05-08
373 / 419
Redeem_a_code_response_information
{ 
  "amount": 0, 
  "identityNo": "string", 
  "referenceNo": "string", 
  "token": "string" 
} 
 
Redeem a code response information
42.675. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
valid
identityNo
string
false
none
historical identify no
referenceNo
string
false
none
Reference Number.
token
string
false
none
valid
Reponse_to_identify_whether_the_binance_code_is_valid.
{ 
  "amount": 0, 
  "isCashPickup": true, 
  "minterInfo": { 
    "country": "string", 
    "dob": "string", 
    "fullName": "string", 
    "state": "string" 
  }, 
  "token": "string", 
  "valid": true 
} 
 
Reponse to identify whether the binance code is valid.
42.676. Properties
Name
Type
Required
Restrictions
Description
amount
number
false
none
amount
isCashPickup
boolean
false
none
isCashPickup
minterInfo
MinterInfo
false
none
minterInfo
token
string
false
none
token
valid
boolean
false
none
valid
Request_parameters_for_Ads_Status_Batch_Update
{ 
  "advNos": [ 
    "string" 
  ], 
  "advStatus": 0 
} 
 
Request parameters for Ads Status Batch Update
42.677. Properties
Name
Type
Required
Restrictions
Description
advNos
[string]
true
none
Ads No
advStatus
integer(int32)
true
none
Ads Status， 1.online，3.offline，4.closed


---

## Page 374

sapi-v7.4.md
2024-05-08
374 / 419
Response_for_creating_a_code_
{ 
  "code": "string", 
  "expiredTime": "2019-08-24T14:15:22Z", 
  "referenceNo": "string" 
} 
 
Response for creating a code
42.678. Properties
Name
Type
Required
Restrictions
Description
code
string
false
none
code
expiredTime
string(date-time)
false
none
Expired Time
referenceNo
string
false
none
Reference Number.
Results_AutoInvestHistoryResp_
{ 
  "list": [ 
    { 
      "executionPrice": 0, 
      "executionType": "string", 
      "failedType": "string", 
      "flexibleUsed": true, 
      "id": 0, 
      "planId": 0, 
      "planName": "string", 
      "planType": "string", 
      "sourceAsset": "string", 
      "sourceAssetAmount": 0, 
      "sourceWallet": "string", 
      "subscriptionCycle": "string", 
      "targetAsset": "string", 
      "targetAssetAmount": 0, 
      "transactionDateTime": 0, 
      "transactionFee": 0, 
      "transactionFeeUnit": "string", 
      "transactionStatus": "string" 
    } 
  ], 
  "total": 0 
} 
 
Results«AutoInvestHistoryResp»
42.679. Properties
Name
Type
Required
Restrictions
Description
list
[AutoInvestHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_BorrowRepayHistoryResp_
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "clientTag": "string", 
      "interest": 0, 
      "isolatedSymbol": "string", 
      "principal": 0, 
      "status": "string", 
      "timestamp": 0, 
      "txId": 0 
    } 


---

## Page 375

sapi-v7.4.md
2024-05-08
375 / 419
  ], 
  "total": 0 
} 
 
Results«BorrowRepayHistoryResp»
42.680. Properties
Name
Type
Required
Restrictions
Description
rows
[BorrowRepayHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_CollateralAssetsDataForSapiResp_
{ 
  "rows": [ 
    { 
      "collateralCoin": "string", 
      "initialLTV": 0, 
      "liquidationLTV": 0, 
      "marginCallLTV": 0, 
      "maxLimit": 0, 
      "vipLevel": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«CollateralAssetsDataForSapiResp»
42.681. Properties
Name
Type
Required
Restrictions
Description
rows
[CollateralAssetsDataForSapiResp]
false
none
none
total
integer(int64)
false
none
none
Results_CollateralRecordResp_
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "createTime": 0, 
      "productName": "string", 
      "status": "string", 
      "type": "string" 
    } 
  ], 
  "total": 0 
} 
 
Results«CollateralRecordResp»
42.682. Properties
Name
Type
Required
Restrictions
Description
rows
[CollateralRecordResp]
false
none
none
total
integer(int64)
false
none
none
Results_ExchangeSmallLiabilityHistoryDto_
{ 
  "rows": [ 


---

## Page 376

sapi-v7.4.md
2024-05-08
376 / 419
    { 
      "amount": 0, 
      "asset": "string", 
      "bizType": "string", 
      "targetAmount": 0, 
      "targetAsset": "string", 
      "timestamp": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«ExchangeSmallLiabilityHistoryDto»
42.683. Properties
Name
Type
Required
Restrictions
Description
rows
[ExchangeSmallLiabilityHistoryDto]
false
none
none
total
integer(int64)
false
none
none
Results_FlexCollateralAssetsDataForSapiResp_
{ 
  "rows": [ 
    { 
      "collateralCoin": "string", 
      "initialLTV": 0, 
      "liquidationLTV": 0, 
      "marginCallLTV": 0, 
      "maxLimit": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«FlexCollateralAssetsDataForSapiResp»
42.684. Properties
Name
Type
Required
Restrictions
Description
rows
[FlexCollateralAssetsDataForSapiResp]
false
none
none
total
integer(int64)
false
none
none
Results_FlexIsoAdjustCollateralHistoryResp_
{ 
  "rows": [ 
    { 
      "adjustTime": 0, 
      "afterLTV": 0, 
      "collateralAmount": 0, 
      "collateralCoin": "string", 
      "direction": "string", 
      "loanCoin": "string", 
      "preLTV": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«FlexIsoAdjustCollateralHistoryResp»
42.685. Properties
Name
Type
Required
Restrictions
Description
rows
[FlexIsoAdjustCollateralHistoryResp]
false
none
none


---

## Page 377

sapi-v7.4.md
2024-05-08
377 / 419
Name
Type
Required
Restrictions
Description
total
integer(int64)
false
none
none
Results_FlexIsoBorrowHistoryResp_
{ 
  "rows": [ 
    { 
      "borrowTime": 0, 
      "collateralCoin": "string", 
      "initialCollateralAmount": 0, 
      "initialLoanAmount": 0, 
      "loanCoin": "string", 
      "status": "string" 
    } 
  ], 
  "total": 0 
} 
 
Results«FlexIsoBorrowHistoryResp»
42.686. Properties
Name
Type
Required
Restrictions
Description
rows
[FlexIsoBorrowHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_FlexIsoCollateralAssetsDataForSapiResp_
{ 
  "rows": [ 
    { 
      "collateralCoin": "string", 
      "initialLTV": 0, 
      "liquidationLTV": 0, 
      "marginCallLTV": 0, 
      "maxLimit": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«FlexIsoCollateralAssetsDataForSapiResp»
42.687. Properties
Name
Type
Required
Restrictions
Description
rows
[FlexIsoCollateralAssetsDataForSapiResp]
false
none
none
total
integer(int64)
false
none
none
Results_FlexIsoLoanableAssetsDataForSapiResp_
{ 
  "rows": [ 
    { 
      "flexibleInterestRate": 0, 
      "flexibleMaxLimit": 0, 
      "flexibleMinLimit": 0, 
      "loanCoin": "string" 
    } 
  ], 
  "total": 0 
} 
 
Results«FlexIsoLoanableAssetsDataForSapiResp»


---

## Page 378

sapi-v7.4.md
2024-05-08
378 / 419
42.688. Properties
Name
Type
Required
Restrictions
Description
rows
[FlexIsoLoanableAssetsDataForSapiResp]
false
none
none
total
integer(int64)
false
none
none
Results_FlexIsoOngoingOrderResp_
{ 
  "rows": [ 
    { 
      "collateralAmount": 0, 
      "collateralCoin": "string", 
      "currentLTV": 0, 
      "loanCoin": "string", 
      "totalDebt": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«FlexIsoOngoingOrderResp»
42.689. Properties
Name
Type
Required
Restrictions
Description
rows
[FlexIsoOngoingOrderResp]
false
none
none
total
integer(int64)
false
none
none
Results_FlexIsoRepayHistoryResp_
{ 
  "rows": [ 
    { 
      "collateralCoin": "string", 
      "collateralReturn": 0, 
      "loanCoin": "string", 
      "repayAmount": 0, 
      "repayStatus": "string", 
      "repayTime": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«FlexIsoRepayHistoryResp»
42.690. Properties
Name
Type
Required
Restrictions
Description
rows
[FlexIsoRepayHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_FlexLoanableAssetsDataForSapiResp_
{ 
  "rows": [ 
    { 
      "flexibleInterestRate": 0, 
      "flexibleMaxLimit": 0, 
      "flexibleMinLimit": 0, 
      "loanCoin": "string" 
    } 
  ], 
  "total": 0 


---

## Page 379

sapi-v7.4.md
2024-05-08
379 / 419
} 
 
Results«FlexLoanableAssetsDataForSapiResp»
42.691. Properties
Name
Type
Required
Restrictions
Description
rows
[FlexLoanableAssetsDataForSapiResp]
false
none
none
total
integer(int64)
false
none
none
Results_FlexibleProductResp_
{ 
  "rows": [ 
    { 
      "airDropPercentageRate": 0, 
      "asset": "string", 
      "canPurchase": true, 
      "canRedeem": true, 
      "hot": true, 
      "isSoldOut": true, 
      "latestAnnualPercentageRate": 0, 
      "minPurchaseAmount": 0, 
      "productId": "string", 
      "status": "CREATED", 
      "subscriptionStartTime": 0, 
      "tierAnnualPercentageRate": { 
        "property1": "string", 
        "property2": "string" 
      } 
    } 
  ], 
  "total": 0 
} 
 
Results«FlexibleProductResp»
42.692. Properties
Name
Type
Required
Restrictions
Description
rows
[FlexibleProductResp]
false
none
none
total
integer(int64)
false
none
none
Results_ForceOrderResp_
{ 
  "rows": [ 
    { 
      "avgPrice": 0, 
      "executedQty": 0, 
      "isIsolated": true, 
      "orderId": 0, 
      "price": 0, 
      "qty": 0, 
      "side": "BUY", 
      "symbol": "string", 
      "time": 0, 
      "timeInForce": "FOK", 
      "updatedTime": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«ForceOrderResp»
42.693. Properties


---

## Page 380

sapi-v7.4.md
2024-05-08
380 / 419
Name
Type
Required
Restrictions
Description
Name
Type
Required
Restrictions
Description
rows
[ForceOrderResp]
false
none
none
total
integer(int64)
false
none
none
Results_InterestHistoryResp_
{ 
  "rows": [ 
    { 
      "asset": "string", 
      "interest": 0, 
      "interestAccruedTime": 0, 
      "interestRate": 0, 
      "principal": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«InterestHistoryResp»
42.694. Properties
Name
Type
Required
Restrictions
Description
rows
[InterestHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanCCAdjustCollateralHistoryResp_
{ 
  "rows": [ 
    { 
      "adjustTime": 0, 
      "afterCollateralRate": 0, 
      "amount": 0, 
      "coin": "string", 
      "collateralCoin": "string", 
      "direction": "ADDITIONAL", 
      "preCollateralRate": 0, 
      "status": "COMPLETED" 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanCCAdjustCollateralHistoryResp»
42.695. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanCCAdjustCollateralHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanCCBorrowHistoryResp_
{ 
  "rows": [ 
    { 
      "borrowId": "string", 
      "coin": "string", 
      "collateralAmount": 0, 
      "collateralCoin": "string", 
      "collateralRate": 0, 
      "confirmedTime": 0, 
      "deadline": 0, 
      "leftPrincipal": 0, 


---

## Page 381

sapi-v7.4.md
2024-05-08
381 / 419
      "leftTotal": 0, 
      "orderStatus": "string" 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanCCBorrowHistoryResp»
42.696. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanCCBorrowHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanCCInterestHistoryResp_
{ 
  "rows": [ 
    { 
      "collateralCoin": "string", 
      "interest": 0, 
      "interestCoin": "string", 
      "interestFreeLimitUsed": 0, 
      "interestRate": 0, 
      "principalForInterest": 0, 
      "time": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanCCInterestHistoryResp»
42.697. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanCCInterestHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanCCLiquidationHistoryResp_
{ 
  "rows": [ 
    { 
      "coin": "string", 
      "collateralAmountForLiquidation": 0, 
      "collateralCoin": "string", 
      "forceLiquidationStartTime": 0, 
      "restCollateralAmountAfterLiquidation": 0, 
      "restLoanAmount": 0, 
      "status": "CLOSED" 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanCCLiquidationHistoryResp»
42.698. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanCCLiquidationHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanCCRepayHistoryResp_


---

## Page 382

sapi-v7.4.md
2024-05-08
382 / 419
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "coin": "string", 
      "collateralAmount": 0, 
      "collateralCoin": "string", 
      "confirmedTime": 0, 
      "price": 0, 
      "releasedCollateral": 0, 
      "repayCollateral": 0, 
      "repayId": "string", 
      "repayType": "string", 
      "status": "string", 
      "updateTime": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanCCRepayHistoryResp»
42.699. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanCCRepayHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanFlexAdjustCollateralHistoryResp_
{ 
  "rows": [ 
    { 
      "adjustTime": 0, 
      "afterLTV": 0, 
      "collateralAmount": 0, 
      "collateralCoin": "string", 
      "direction": "string", 
      "loanCoin": "string", 
      "preLTV": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanFlexAdjustCollateralHistoryResp»
42.700. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanFlexAdjustCollateralHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanFlexBorrowHistoryResp_
{ 
  "rows": [ 
    { 
      "borrowTime": 0, 
      "collateralCoin": "string", 
      "initialCollateralAmount": 0, 
      "initialLoanAmount": 0, 
      "loanCoin": "string", 
      "status": "string" 
    } 
  ], 
  "total": 0 
} 
 


---

## Page 383

sapi-v7.4.md
2024-05-08
383 / 419
Results«LoanFlexBorrowHistoryResp»
42.701. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanFlexBorrowHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanFlexOngoingOrderResp_
{ 
  "rows": [ 
    { 
      "collateralAmount": 0, 
      "collateralCoin": "string", 
      "currentLTV": 0, 
      "loanCoin": "string", 
      "totalDebt": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanFlexOngoingOrderResp»
42.702. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanFlexOngoingOrderResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanFlexRepayHistoryResp_
{ 
  "rows": [ 
    { 
      "collateralCoin": "string", 
      "collateralReturn": 0, 
      "loanCoin": "string", 
      "repayAmount": 0, 
      "repayStatus": "string", 
      "repayTime": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanFlexRepayHistoryResp»
42.703. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanFlexRepayHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanOtcAccountInfoResp_
{ 
  "rows": [ 
    { 
      "collateralAccountId": 0, 
      "collateralCoin": "string" 
    } 
  ], 
  "total": 0 


---

## Page 384

sapi-v7.4.md
2024-05-08
384 / 419
} 
 
Results«LoanOtcAccountInfoResp»
42.704. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanOtcAccountInfoResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanOtcOngoingOrdersResp_
{ 
  "rows": [ 
    { 
      "collateralAccountId": "string", 
      "collateralCoin": "string", 
      "collateralValue": 0, 
      "currentLTV": 0, 
      "expirationTime": 0, 
      "initialLtv": "string", 
      "liquidationLtv": "string", 
      "loanCoin": "string", 
      "loanDate": "string", 
      "loanRate": "string", 
      "loanTerm": "string", 
      "lockedCollateralValue": 0, 
      "marginCallLtv": "string", 
      "orderId": 0, 
      "residualInterest": 0, 
      "totalCollateralValueAfterHaircut": 0, 
      "totalDebt": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanOtcOngoingOrdersResp»
42.705. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanOtcOngoingOrdersResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanOtcRepayHistoryResp_
{ 
  "rows": [ 
    { 
      "collateralCoin": "string", 
      "loanCoin": "string", 
      "loanDate": 0, 
      "orderId": 0, 
      "repayAmount": 0, 
      "repayStatus": "string", 
      "repayTime": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanOtcRepayHistoryResp»
42.706. Properties
Name
Type
Required
Restrictions
Description


---

## Page 385

sapi-v7.4.md
2024-05-08
385 / 419
Name
Type
Required
Restrictions
Description
rows
[LoanOtcRepayHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanOtcRequestStatusResp_
{ 
  "rows": [ 
    { 
      "collateralAccountId": "string", 
      "collateralCoin": "string", 
      "loanAccountId": 0, 
      "loanAmount": 0, 
      "loanCoin": "string", 
      "loanDate": 0, 
      "loanTerm": 0, 
      "orderId": 0, 
      "reason": "string", 
      "requestId": 0, 
      "status": "string" 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanOtcRequestStatusResp»
42.707. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanOtcRequestStatusResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanRetailAdjustCollateralHistoryResp_
{ 
  "rows": [ 
    { 
      "adjustTime": 0, 
      "afterLTV": 0, 
      "amount": 0, 
      "collateralCoin": "string", 
      "direction": "string", 
      "loanCoin": "string", 
      "orderId": 0, 
      "preLTV": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanRetailAdjustCollateralHistoryResp»
42.708. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanRetailAdjustCollateralHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanRetailBorrowHistoryResp_
{ 
  "rows": [ 
    { 
      "borrowTime": 0, 
      "collateralCoin": "string", 


---

## Page 386

sapi-v7.4.md
2024-05-08
386 / 419
      "hourlyInterestRate": 0, 
      "initialCollateralAmount": 0, 
      "initialLoanAmount": 0, 
      "loanCoin": "string", 
      "loanTerm": 0, 
      "orderId": 0, 
      "status": "string" 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanRetailBorrowHistoryResp»
42.709. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanRetailBorrowHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanRetailOngoingOrdersResp_
{ 
  "rows": [ 
    { 
      "collateralAmount": 0, 
      "collateralCoin": "string", 
      "currentLTV": 0, 
      "expirationTime": 0, 
      "loanCoin": "string", 
      "orderId": 0, 
      "residualInterest": 0, 
      "totalDebt": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanRetailOngoingOrdersResp»
42.710. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanRetailOngoingOrdersResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanRetailRepayHistoryResp_
{ 
  "rows": [ 
    { 
      "collateralCoin": "string", 
      "collateralReturn": 0, 
      "collateralUsed": 0, 
      "loanCoin": "string", 
      "orderId": 0, 
      "repayAmount": 0, 
      "repayStatus": "string", 
      "repayTime": 0, 
      "repayType": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanRetailRepayHistoryResp»
42.711. Properties


---

## Page 387

sapi-v7.4.md
2024-05-08
387 / 419
Name
Type
Required
Restrictions
Description
rows
[LoanRetailRepayHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_LoanableAssetsDataForSapiResp_
{ 
  "rows": [ 
    { 
      "_14dDailyInterestRate": 0, 
      "_14dHourlyInterestRate": 0, 
      "_180dDailyInterestRate": 0, 
      "_180dHourlyInterestRate": 0, 
      "_30dDailyInterestRate": 0, 
      "_30dHourlyInterestRate": 0, 
      "_7dDailyInterestRate": 0, 
      "_7dHourlyInterestRate": 0, 
      "_90dDailyInterestRate": 0, 
      "_90dHourlyInterestRate": 0, 
      "loanCoin": "string", 
      "maxLimit": 0, 
      "minLimit": 0, 
      "vipLevel": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«LoanableAssetsDataForSapiResp»
42.712. Properties
Name
Type
Required
Restrictions
Description
rows
[LoanableAssetsDataForSapiResp]
false
none
none
total
integer(int64)
false
none
none
Results_MgsBorrowHistoryDtoV2_
{ 
  "rows": [ 
    { 
      "asset": "string", 
      "clientTag": "string", 
      "isolatedSymbol": "string", 
      "principal": 0, 
      "status": "CONFIRMED", 
      "timestamp": 0, 
      "txId": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«MgsBorrowHistoryDtoV2»
42.713. Properties
Name
Type
Required
Restrictions
Description
rows
[MgsBorrowHistoryDtoV2]
false
none
none
total
integer(int64)
false
none
none
Results_MgsRepayHistoryDtoV2_
{ 
  "rows": [ 
    { 


---

## Page 388

sapi-v7.4.md
2024-05-08
388 / 419
      "amount": 0, 
      "asset": "string", 
      "clientTag": "string", 
      "interest": 0, 
      "isolatedSymbol": "string", 
      "principal": 0, 
      "status": "CONFIRMED", 
      "timestamp": 0, 
      "txId": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«MgsRepayHistoryDtoV2»
42.714. Properties
Name
Type
Required
Restrictions
Description
rows
[MgsRepayHistoryDtoV2]
false
none
none
total
integer(int64)
false
none
none
Results_PositionResp_
{ 
  "rows": [ 
    { 
      "accrualDays": 0, 
      "amount": 0, 
      "apy": 0, 
      "asset": "string", 
      "canFastRedemption": true, 
      "canReStake": true, 
      "canRedeemEarly": true, 
      "deliverDate": 0, 
      "duration": 0, 
      "estExtraRewardAmt": 0, 
      "extraRewardAPY": 0, 
      "extraRewardAsset": "string", 
      "interestEndDate": 0, 
      "nextInterestPay": 0, 
      "nextInterestPayDate": 0, 
      "partialAmtDeliverDate": 0, 
      "payInterestPeriod": 0, 
      "positionId": 0, 
      "productId": "string", 
      "purchaseTime": 0, 
      "redeemAmountEarly": 0, 
      "redeemPeriod": 0, 
      "redeemingAmt": 0, 
      "renewable": true, 
      "rewardAmt": 0, 
      "rewardAsset": "string", 
      "status": "string", 
      "type": "string" 
    } 
  ], 
  "total": 0 
} 
 
Results«PositionResp»
42.715. Properties
Name
Type
Required
Restrictions
Description
rows
[PositionResp]
false
none
none
total
integer(int64)
false
none
none
Results_RateHistoryResp_


---

## Page 389

sapi-v7.4.md
2024-05-08
389 / 419
{ 
  "rows": [ 
    { 
      "annualPercentageRate": 0, 
      "asset": "string", 
      "productId": "string", 
      "time": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«RateHistoryResp»
42.716. Properties
Name
Type
Required
Restrictions
Description
rows
[RateHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_RedemptionRecordResp_
{ 
  "rows": [ 
    { 
      "rows": [ 
        { 
          "amount": 0, 
          "asset": "string", 
          "deliverDate": 0, 
          "lockPeriod": 0, 
          "positionId": 0, 
          "redeemId": 0, 
          "status": "string", 
          "time": 0, 
          "type": "string" 
        } 
      ], 
      "total": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«RedemptionRecordResp»
42.717. Properties
Name
Type
Required
Restrictions
Description
rows
[RedemptionRecordResp]
false
none
none
total
integer(int64)
false
none
none
Results_RewardsRecordResp_
{ 
  "rows": [ 
    { 
      "rows": [ 
        { 
          "amount": 0, 
          "asset": "string", 
          "lockPeriod": 0, 
          "positionId": 0, 
          "time": 0 
        } 
      ], 
      "total": 0 
    } 
  ], 


---

## Page 390

sapi-v7.4.md
2024-05-08
390 / 419
  "total": 0 
} 
 
Results«RewardsRecordResp»
42.718. Properties
Name
Type
Required
Restrictions
Description
rows
[RewardsRecordResp]
false
none
none
total
integer(int64)
false
none
none
Results_SetRetailCustomedMarginCallRateForSapiResp_
{ 
  "rows": [ 
    { 
      "afterMarginCall": 0, 
      "collateralCoin": "string", 
      "customizeTime": 0, 
      "orderId": 0, 
      "preMarginCall": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«SetRetailCustomedMarginCallRateForSapiResp»
42.719. Properties
Name
Type
Required
Restrictions
Description
rows
[SetRetailCustomedMarginCallRateForSapiResp]
false
none
none
total
integer(int64)
false
none
none
Results_SubscriptionRecordResp_
{ 
  "rows": [ 
    { 
      "rows": [ 
        { 
          "amount": 0, 
          "amtFromFunding": 0, 
          "amtFromSpot": 0, 
          "asset": "string", 
          "lockPeriod": 0, 
          "positionId": 0, 
          "projectId": "string", 
          "purchaseId": 0, 
          "sourceAccount": "string", 
          "status": "string", 
          "time": 0, 
          "type": "string" 
        } 
      ], 
      "total": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«SubscriptionRecordResp»
42.720. Properties
Name
Type
Required
Restrictions
Description


---

## Page 391

sapi-v7.4.md
2024-05-08
391 / 419
Name
Type
Required
Restrictions
Description
rows
[SubscriptionRecordResp]
false
none
none
total
integer(int64)
false
none
none
Results_TransferHistoryResp_
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "fromSymbol": "string", 
      "status": "string", 
      "timestamp": 0, 
      "toSymbol": "string", 
      "transFrom": "CROSS_MARGIN", 
      "transTo": "CROSS_MARGIN", 
      "transferCounterparty": "string", 
      "txId": 0, 
      "type": "string" 
    } 
  ], 
  "total": 0 
} 
 
Results«TransferHistoryResp»
42.721. Properties
Name
Type
Required
Restrictions
Description
rows
[TransferHistoryResp]
false
none
none
total
integer(int64)
false
none
none
Results_TransferQueryResp_
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "clientTag": "string", 
      "fromSymbol": "string", 
      "status": "string", 
      "timestamp": 0, 
      "toSymbol": "string", 
      "transFrom": "string", 
      "transTo": "string", 
      "txId": 0, 
      "type": "BORROW" 
    } 
  ], 
  "total": 0 
} 
 
Results«TransferQueryResp»
42.722. Properties
Name
Type
Required
Restrictions
Description
rows
[TransferQueryResp]
false
none
none
total
integer(int64)
false
none
none
Results_VipCollateralAssetsDataForSapiResp_
{ 
  "rows": [ 


---

## Page 392

sapi-v7.4.md
2024-05-08
392 / 419
    { 
      "_1stCollateralRange": "string", 
      "_1stCollateralRatio": "string", 
      "_2ndCollateralRange": "string", 
      "_2ndCollateralRatio": "string", 
      "_3rdCollateralRange": "string", 
      "_3rdCollateralRatio": "string", 
      "_4thCollateralRange": "string", 
      "_4thCollateralRatio": "string", 
      "_5thCollateralRange": "string", 
      "_5thCollateralRatio": "string", 
      "_6thCollateralRange": "string", 
      "_6thCollateralRatio": "string", 
      "_7thCollateralRange": "string", 
      "_7thCollateralRatio": "string", 
      "_8thCollateralRange": "string", 
      "_8thCollateralRatio": "string", 
      "_9thCollateralRange": "string", 
      "_9thCollateralRatio": "string", 
      "collateralCoin": "string" 
    } 
  ], 
  "total": 0 
} 
 
Results«VipCollateralAssetsDataForSapiResp»
42.723. Properties
Name
Type
Required
Restrictions
Description
rows
[VipCollateralAssetsDataForSapiResp]
false
none
none
total
integer(int64)
false
none
none
Results_VipLoanableAssetsDataForSapiResp_
{ 
  "rows": [ 
    { 
      "_30dDailyInterestRate": 0, 
      "_30dYearlyInterestRate": 0, 
      "_60dDailyInterestRate": 0, 
      "_60dYearlyInterestRate": 0, 
      "_flexibleDailyInterestRate": 0, 
      "_flexibleHourlyInterestRate": 0, 
      "_flexibleYearlyInterestRate": 0, 
      "loanCoin": "string", 
      "maxLimit": 0, 
      "minLimit": 0, 
      "vipLevel": 0 
    } 
  ], 
  "total": 0 
} 
 
Results«VipLoanableAssetsDataForSapiResp»
42.724. Properties
Name
Type
Required
Restrictions
Description
rows
[VipLoanableAssetsDataForSapiResp]
false
none
none
total
integer(int64)
false
none
none
SearchResult_BrokerFreezeLogResponse_
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "brokerParentId": 0, 


---

## Page 393

sapi-v7.4.md
2024-05-08
393 / 419
      "brokerSubAccountId": 0, 
      "clientTransId": "string", 
      "operateType": "FREEZE", 
      "status": "FAILURE", 
      "time": 0, 
      "tranId": "string" 
    } 
  ], 
  "total": 0 
} 
 
SearchResult«BrokerFreezeLogResponse»
42.725. Properties
Name
Type
Required
Restrictions
Description
rows
[BrokerFreezeLogResponse]
false
none
none
total
integer(int64)
false
none
none
SearchResult_BrokerSettlementLogResponse_
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "brokerParentId": 0, 
      "brokerSubAccountId": 0, 
      "clientTransId": "string", 
      "recipientSubAccountId": 0, 
      "status": "FAILURE", 
      "time": 0, 
      "tranId": "string" 
    } 
  ], 
  "total": 0 
} 
 
SearchResult«BrokerSettlementLogResponse»
42.726. Properties
Name
Type
Required
Restrictions
Description
rows
[BrokerSettlementLogResponse]
false
none
none
total
integer(int64)
false
none
none
SearchResult_MMQueryProductItem_
{ 
  "rows": [ 
    { 
      "brandingId": 0, 
      "brandingName": "string", 
      "buyoutPrice": 0, 
      "collectionId": 0, 
      "collectionName": "string", 
      "contractAddress": "string", 
      "creator": "string", 
      "currency": "string", 
      "expireDate": "2019-08-24T14:15:22Z", 
      "itemId": 0, 
      "itemName": "string", 
      "network": "string", 
      "nftType": 0, 
      "orderType": 0, 
      "owner": "string", 
      "productId": 0, 
      "rarity": 0, 
      "startingPrice": 0, 
      "title": "string", 


---

## Page 394

sapi-v7.4.md
2024-05-08
394 / 419
      "tokenId": "string" 
    } 
  ], 
  "total": 0 
} 
 
SearchResult«MMQueryProductItem»
42.727. Properties
Name
Type
Required
Restrictions
Description
rows
[MMQueryProductItem]
false
none
none
total
integer(int64)
false
none
none
SearchResult_OtcSymbolSelector_
{ 
  "rows": [ 
    { 
      "base": "string", 
      "baseMax": 0, 
      "baseMin": 0, 
      "quote": "string", 
      "quoteMax": 0, 
      "quoteMin": 0, 
      "trade": "string" 
    } 
  ], 
  "total": 0 
} 
 
SearchResult«OtcSymbolSelector»
42.728. Properties
Name
Type
Required
Restrictions
Description
rows
[OtcSymbolSelector]
false
none
none
total
integer(int64)
false
none
none
SearchResult_ThirdPartyNftAssetVo_
{ 
  "rows": [ 
    { 
      "assetStatus": "string", 
      "assetType": "string", 
      "brandingId": 0, 
      "brandingName": "string", 
      "buyOutPrice": 0, 
      "collectionId": 0, 
      "collectionName": "string", 
      "contractAddress": "string", 
      "creatorName": "string", 
      "currency": "string", 
      "expireDate": 0, 
      "itemTypeId": 0, 
      "itemTypeName": "string", 
      "listingOrderNumber": 0, 
      "nftInfoId": 0, 
      "orderType": "string", 
      "ownerName": "string", 
      "productId": 0, 
      "rarity": "string", 
      "startingPrice": 0, 
      "tokenId": "string" 
    } 
  ], 
  "total": 0 
} 
 


---

## Page 395

sapi-v7.4.md
2024-05-08
395 / 419
SearchResult«ThirdPartyNftAssetVo»
42.729. Properties
Name
Type
Required
Restrictions
Description
rows
[ThirdPartyNftAssetVo]
false
none
none
total
integer(int64)
false
none
none
SubAccountAssetResp_SubAccountFuturesAssetResp_
{ 
  "data": [ 
    { 
      "futuresEnable": true, 
      "subAccountId": "string", 
      "totalInitialMarginOfUsdt": "string", 
      "totalMaintenanceMarginOfUsdt": "string", 
      "totalMarginBalanceOfUsdt": "string", 
      "totalOpenOrderInitialMarginOfUsdt": "string", 
      "totalPositionInitialMarginOfUsdt": "string", 
      "totalUnrealizedProfitOfUsdt": "string", 
      "totalWalletBalanceOfUsdt": "string" 
    } 
  ], 
  "timestamp": 0 
} 
 
SubAccountAssetResp«SubAccountFuturesAssetResp»
42.730. Properties
Name
Type
Required
Restrictions
Description
data
[SubAccountFuturesAssetResp]
false
none
⼦账户资产列表
timestamp
integer(int64)
false
none
查询时间（UTC）
SubAccountAssetResp_SubAccountMarginAssetResp_
{ 
  "data": [ 
    { 
      "marginEnable": true, 
      "marginLevel": "string", 
      "subAccountId": "string", 
      "totalAssetOfBtc": "string", 
      "totalLiabilityOfBtc": "string", 
      "totalNetAssetOfBtc": "string" 
    } 
  ], 
  "timestamp": 0 
} 
 
SubAccountAssetResp«SubAccountMarginAssetResp»
42.731. Properties
Name
Type
Required
Restrictions
Description
data
[SubAccountMarginAssetResp]
false
none
⼦账户资产列表
timestamp
integer(int64)
false
none
查询时间（UTC）
SubAccountAssetResp_SubAccountSpotAssetResp_
{ 
  "data": [ 
    { 
      "subAccountId": "string", 


---

## Page 396

sapi-v7.4.md
2024-05-08
396 / 419
      "totalBalanceOfBtc": "string" 
    } 
  ], 
  "timestamp": 0 
} 
 
SubAccountAssetResp«SubAccountSpotAssetResp»
42.732. Properties
Name
Type
Required
Restrictions
Description
data
[SubAccountSpotAssetResp]
false
none
⼦账户资产列表
timestamp
integer(int64)
false
none
查询时间（UTC）
User_Order_History
{ 
  "additionalKycVerify": 0, 
  "advNo": "string", 
  "advertisementRole": "string", 
  "amount": "string", 
  "asset": "string", 
  "commission": 0, 
  "counterPartNickName": "string", 
  "createTime": "2019-08-24T14:15:22Z", 
  "fiat": "string", 
  "fiatSymbol": "string", 
  "orderNumber": "string", 
  "orderStatus": "string", 
  "payMethodName": "string", 
  "takerAmount": 0, 
  "takerCommission": 0, 
  "takerCommissionRate": 0, 
  "totalPrice": "string", 
  "tradeType": "string", 
  "unitPrice": 0 
} 
 
User Order History
42.733. Properties
Name
Type
Required
Restrictions
Description
additionalKycVerify
integer(int32)
false
none
additional kyc verify: 0 not required 1 not verified 2 verified
advNo
string
false
none
Adv Number
advertisementRole
string
false
none
Advertisement Role: (Maker, Taker)
amount
string
false
none
seller/buyer trade amount = (seller deducted amount - seller fee amount) = (buyer
received amount + buyer fee amount)
asset
string
false
none
Crypto asset: BTC
commission
number
false
none
Actual commission fee of order
counterPartNickName
string
false
none
Counterpart Nick Name
createTime
string(date-
time)
false
none
Order create Time
fiat
string
false
none
Fiat currency: CNY
fiatSymbol
string
false
none
Fiat currency symbol
orderNumber
string
false
none
Order Number
orderStatus
string
false
none
Order status (1: Wait for payment, 2: Wait for release, 3: Appealing, 4: Completed, 6:
Cancelled, 7: Cancelled by system
payMethodName
string
false
none
Identifier of the payment method


---

## Page 397

sapi-v7.4.md
2024-05-08
397 / 419
Name
Type
Required
Restrictions
Description
takerAmount
number
false
none
taker actual deducted/received amount if taker sell: taker amount = seller deducted
amount = (amount + taker_commission), if taker buy: taker amount = buyer received
amount = (amount - taker_commission)
takerCommission
number
false
none
taker actual commission
takerCommissionRate
number
false
none
taker actual commission rate
totalPrice
string
false
none
Order total Price
tradeType
string
false
none
Order trade type. 0: BUY, 1: SELL
unitPrice
number
false
none
Unit Price
VIP_Portal_Batch_Send_Mail_DTO
{ 
  "autoSend": true, 
  "emails": [ 
    "string" 
  ], 
  "filePassword": "string", 
  "ids": [ 
    "string" 
  ], 
  "internal": true, 
  "jobId": "string", 
  "userId": 0 
} 
 
VIP Portal Batch Send Mail DTO
42.734. Properties
Name
Type
Required
Restrictions
Description
autoSend
boolean
false
none
none
emails
[string]
false
none
none
filePassword
string
false
none
none
ids
[string]
false
none
none
internal
boolean
false
none
none
jobId
string
false
none
none
userId
integer(int64)
false
none
none
VIP_Portal_Report_Config_Model
{ 
  "businessType": "string", 
  "fileTypes": [ 
    "string" 
  ], 
  "reportFields": [ 
    "string" 
  ], 
  "reportType": "string" 
} 
 
VIP Portal Report Config Model
42.735. Properties
Name
Type
Required
Restrictions
Description
businessType
string
false
none
none
fileTypes
[string]
false
none
none
reportFields
[string]
false
none
none


---

## Page 398

sapi-v7.4.md
2024-05-08
398 / 419
Name
Type
Required
Restrictions
Description
reportType
string
false
none
none
VIP_Portal_Report_DTO
{ 
  "autoSend": true, 
  "batchSendMail": { 
    "autoSend": true, 
    "emails": [ 
      "string" 
    ], 
    "filePassword": "string", 
    "ids": [ 
      "string" 
    ], 
    "internal": true, 
    "jobId": "string", 
    "userId": 0 
  }, 
  "businessType": "string", 
  "createByUid": 0, 
  "endDate": "string", 
  "fileType": "string", 
  "id": "string", 
  "majorUser": true, 
  "parameters": {}, 
  "reportType": "string", 
  "source": "string", 
  "startDate": "string", 
  "timeZone": "string", 
  "uids": [ 
    "string" 
  ] 
} 
 
VIP Portal Report DTO
42.736. Properties
Name
Type
Required
Restrictions
Description
autoSend
boolean
false
none
Auto Send
batchSendMail
VIP_Portal_Batch_Send_Mail_DTO
false
none
Batch Send Mail DTO
businessType
string
false
none
none
createByUid
integer(int64)
false
none
User Id
endDate
string
false
none
none
fileType
string
false
none
none
id
string
false
none
none
majorUser
boolean
false
none
none
parameters
object
false
none
none
reportType
string
false
none
none
source
string
false
none
Source
startDate
string
false
none
none
timeZone
string
false
none
none
uids
[string]
false
none
none
VIP_Portal_Report_Item_Model
{ 
  "businessType": "string", 
  "createByUid": "string", 
  "dbCreateTime": "2019-08-24T14:15:22Z", 
  "dbModifyTime": "2019-08-24T14:15:22Z", 
  "emails": [ 


---

## Page 399

sapi-v7.4.md
2024-05-08
399 / 419
    "string" 
  ], 
  "endDate": "string", 
  "fileType": "string", 
  "pdfLink": "string", 
  "reportName": "string", 
  "reportType": "string", 
  "reportUrl": "string", 
  "s3Link": "string", 
  "source": "string", 
  "startDate": "string", 
  "status": 0, 
  "timezone": "string", 
  "url": "string", 
  "userId": "string" 
} 
 
VIP Portal Report Item Model
42.737. Properties
Name
Type
Required
Restrictions
Description
businessType
string
false
none
Business Type
createByUid
string
false
none
Create by uid
dbCreateTime
string(date-time)
false
none
Create Time
dbModifyTime
string(date-time)
false
none
Modify Time
emails
[string]
false
none
Emails
endDate
string
false
none
End Date
fileType
string
false
none
File Type
pdfLink
string
false
none
pdf Link
reportName
string
false
none
Report Name
reportType
string
false
none
Report Type
reportUrl
string
false
none
Report Url
s3Link
string
false
none
S3 Link
source
string
false
none
none
startDate
string
false
none
Start Date
status
integer(int32)
false
none
Status
timezone
string
false
none
Timezone
url
string
false
none
Url
userId
string
false
none
User Id
api_
{ 
  "asset": "string", 
  "customerId": "string", 
  "email": "string", 
  "income": "string", 
  "orderId": 0, 
  "symbol": "string", 
  "time": 0, 
  "tradeId": 0 
} 
 
api佣⾦明细结果
42.738. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
资产名称


---

## Page 400

sapi-v7.4.md
2024-05-08
400 / 419
Name
Type
Required
Restrictions
Description
customerId
string
false
none
被推荐⼈对应的三⽅昵称
email
string
false
none
被推荐⼈email账号
income
string
false
none
佣⾦⾦额
orderId
integer(int64)
false
none
订单号
symbol
string
false
none
交易产品名称
time
integer(int64)
false
none
交易时间
tradeId
integer(int64)
false
none
交易订单号
broker_Response
{ 
  "clientTranId": "string", 
  "txnId": 0 
} 
 
broker⼦⺟账户划转Response
42.739. Properties
Name
Type
Required
Restrictions
Description
clientTranId
string
false
none
三⽅交易流⽔号
txnId
integer(int64)
false
none
事务操作id
commission_rate
{ 
  "fiat": "string" 
} 
 
commission rate
42.740. Properties
Name
Type
Required
Restrictions
Description
fiat
string
false
none
fiat currency
commission_rate_overview
{ 
  "assetRetList": [ 
    { 
      "asset": "string", 
      "assetLogoUrl": "string", 
      "assetName": "string", 
      "items": [ 
        { 
          "area": "string", 
          "channel": "string", 
          "fiat": "string", 
          "makerBuyBaseCommissionRate": 0, 
          "makerBuyCommissionRate": 0, 
          "makerSellBaseCommissionRate": 0, 
          "makerSellCommissionRate": 0, 
          "takerBuyBaseCommissionRate": 0, 
          "takerBuyCommissionRate": 0, 
          "takerSellBaseCommissionRate": 0, 
          "takerSellCommissionRate": 0 
        } 
      ] 
    } 
  ], 
  "userDiscountOffRateMaker": 0, 


---

## Page 401

sapi-v7.4.md
2024-05-08
401 / 419
  "userDiscountOffRateTaker": 0, 
  "userLevel": 0 
} 
 
commission rate overview
42.741. Properties
Name
Type
Required
Restrictions
Description
assetRetList
[commission_rate_overview_asset]
false
none
none
userDiscountOffRateMaker
number
false
none
none
userDiscountOffRateTaker
number
false
none
none
userLevel
integer(int32)
false
none
none
commission_rate_overview_asset
{ 
  "asset": "string", 
  "assetLogoUrl": "string", 
  "assetName": "string", 
  "items": [ 
    { 
      "area": "string", 
      "channel": "string", 
      "fiat": "string", 
      "makerBuyBaseCommissionRate": 0, 
      "makerBuyCommissionRate": 0, 
      "makerSellBaseCommissionRate": 0, 
      "makerSellCommissionRate": 0, 
      "takerBuyBaseCommissionRate": 0, 
      "takerBuyCommissionRate": 0, 
      "takerSellBaseCommissionRate": 0, 
      "takerSellCommissionRate": 0 
    } 
  ] 
} 
 
commission rate overview asset
42.742. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
digital currency
assetLogoUrl
string
false
none
asset logo url
assetName
string
false
none
asset name
items
[commission_rate_overview_item]
false
none
commission rate overview item
commission_rate_overview_item
{ 
  "area": "string", 
  "channel": "string", 
  "fiat": "string", 
  "makerBuyBaseCommissionRate": 0, 
  "makerBuyCommissionRate": 0, 
  "makerSellBaseCommissionRate": 0, 
  "makerSellCommissionRate": 0, 
  "takerBuyBaseCommissionRate": 0, 
  "takerBuyCommissionRate": 0, 
  "takerSellBaseCommissionRate": 0, 
  "takerSellCommissionRate": 0 
} 
 
commission rate overview item


---

## Page 402

sapi-v7.4.md
2024-05-08
402 / 419
42.743. Properties
Name
Type
Required
Restrictions
Description
area
string
false
none
area: express/p2pZone/blockZone/cashZone/shareAds/other
channel
string
false
none
channel: c2c/pay/fiatCashier/fiatPass/fiatPeer/lite
fiat
string
false
none
fiat currency
makerBuyBaseCommissionRate
number
false
none
maker buy commission base rate
makerBuyCommissionRate
number
false
none
maker buy commission rate
makerSellBaseCommissionRate
number
false
none
maker sell commission base rate
makerSellCommissionRate
number
false
none
maker sell commission rate
takerBuyBaseCommissionRate
number
false
none
taker buy commission base rate
takerBuyCommissionRate
number
false
none
taker buy commission rate
takerSellBaseCommissionRate
number
false
none
taker sell commission base rate
takerSellCommissionRate
number
false
none
taker sell commission rate
sapi_
{ 
  "fromAsset": "string", 
  "fromAssetMaxAmount": 0, 
  "fromAssetMinAmount": 0, 
  "fromIsBase": true, 
  "toAsset": "string", 
  "toAssetMaxAmount": 0, 
  "toAssetMinAmount": 0 
} 
 
sapi选择器
42.744. Properties
Name
Type
Required
Restrictions
Description
fromAsset
string
false
none
fromAsset
fromAssetMaxAmount
number
false
none
fromAsset最⼤⾦额
fromAssetMinAmount
number
false
none
fromAsset最⼩⾦额
fromIsBase
boolean
false
none
if fromAsset is baseAsset
toAsset
string
false
none
toAsset
toAssetMaxAmount
number
false
none
toAsset最⼤⾦额
toAssetMinAmount
number
false
none
toAsset最⼩⾦额
taker_commission_rate
{ 
  "baseCommissionRate": 0, 
  "commissionRate": 0, 
  "tradeMethodIdentifier": "string", 
  "tradeType": "string" 
} 
 
taker commission rate
42.745. Properties
Name
Type
Required
Restrictions
Description
baseCommissionRate
number
false
none
commission base rate
commissionRate
number
false
none
commission rate
tradeMethodIdentifier
string
false
none
trade method identifier


---

## Page 403

sapi-v7.4.md
2024-05-08
403 / 419
Name
Type
Required
Restrictions
Description
tradeType
string
false
none
taker trade type，BUY/SELL
taker_commission_rate0
{ 
  "area": "string", 
  "asset": "string", 
  "classify": "string", 
  "fiat": "string", 
  "tradeMethodIdentifier": [ 
    "string" 
  ], 
  "tradeType": "string" 
} 
 
taker commission rate0
42.746. Properties
Name
Type
Required
Restrictions
Description
area
string
false
none
area: express/p2pZone
asset
string
false
none
digital currency
classify
string
false
none
adv classify: block/mass/profession
fiat
string
false
none
fiat currency
tradeMethodIdentifier
[string]
false
none
trade method identifier
tradeType
string
false
none
taker trade type，buy/sell
transfer_response
{ 
  "response": "string", 
  "status": "string", 
  "tranId": 0 
} 
 
transfer response
42.747. Properties
Name
Type
Required
Restrictions
Description
response
string
false
none
status如果不为S, 撮合返回的response，仅供调⽤⽅参考，⽅便排查问题
status
string
false
none
reverse transaction状态
tranId
integer(int64)
false
none
tran id
_
{ 
  "bgColor": "string", 
  "chatNeed": 0, 
  "createTime": "2019-08-24T14:15:22Z", 
  "iconUrlColor": "string", 
  "iconUrlGray": "string", 
  "id": 0, 
  "identifier": "string", 
  "isOnline": 0, 
  "isRecommended": 0, 
  "isVisible": 0, 
  "multiAllow": 0, 
  "name": "string", 
  "nameKey": "string", 
  "remark": "string", 
  "risk": "string", 


---

## Page 404

sapi-v7.4.md
2024-05-08
404 / 419
  "riskKey": "string", 
  "riskLevel": 0, 
  "sequence": 0, 
  "shortName": "string", 
  "shortNameKey": "string", 
  "tradeMethodCode": 0, 
  "typeCode": "string", 
  "typeName": "string", 
  "updateTime": "2019-08-24T14:15:22Z" 
} 
 
交易⽅式
42.748. Properties
Name
Type
Required
Restrictions
Description
bgColor
string
false
none
背景颜⾊
chatNeed
integer(int32)
false
none
是否需要chat
createTime
string(date-time)
false
none
创建时间
iconUrlColor
string
false
none
带背景颜⾊图标
iconUrlGray
string
false
none
不带背景颜⾊图标
id
integer(int64)
false
none
主键id
identifier
string
false
none
唯⼀标识
isOnline
integer(int32)
false
none
is online payment
isRecommended
integer(int32)
false
none
是否推荐
isVisible
integer(int32)
false
none
是否可⻅
multiAllow
integer(int32)
false
none
是否允许多选
name
string
false
none
none
nameKey
string
false
none
none
remark
string
false
none
备注
risk
string
false
none
none
riskKey
string
false
none
none
riskLevel
integer(int32)
false
none
⻛险等级
sequence
integer(int32)
false
none
序列号
shortName
string
false
none
none
shortNameKey
string
false
none
none
tradeMethodCode
integer(int64)
false
none
兼容pay_method.pay_type
typeCode
string
false
none
交易⽅式类型编码
typeName
string
false
none
交易⽅式类型名称
updateTime
string(date-time)
false
none
修改时间
_convert_
{ 
  "convert": true, 
  "subAccountId": "string", 
  "updateTime": 0 
} 
 
修改convert权限返回结果
42.749. Properties
Name
Type
Required
Restrictions
Description
convert
boolean
false
none
是否拥有convert权限


---

## Page 405

sapi-v7.4.md
2024-05-08
405 / 419
Name
Type
Required
Restrictions
Description
subAccountId
string
false
none
broke⼦账号Id
updateTime
integer(int64)
false
none
更新时间
_apiKey_
{ 
  "apiName": "string", 
  "apikey": "string", 
  "canFuturesTrade": true, 
  "canMarginLoanRepay": true, 
  "canTrade": true, 
  "canUniversalTransfer": true, 
  "canVanillaOptions": true, 
  "timestamp": 0 
} 
 
修改⼦账户apiKey权限
42.750. Properties
Name
Type
Required
Restrictions
Description
apiName
string
false
none
API名称
apikey
string
false
none
apikey
canFuturesTrade
boolean
false
none
canFuturesTrade
canMarginLoanRepay
boolean
false
none
canMarginLoanRepay
canTrade
boolean
false
none
canTrade
canUniversalTransfer
boolean
false
none
canUniversalTransfer
canVanillaOptions
boolean
false
none
canVanillaOptions
timestamp
integer(int64)
false
none
时间戳
_ConvertTransferPageResp_
{ 
  "rows": [ 
    { 
      "accountType": "string", 
      "deductedAmount": 0, 
      "deductedAsset": "string", 
      "status": "string", 
      "targetAmount": 0, 
      "targetAsset": "string", 
      "time": "2019-08-24T14:15:22Z", 
      "tranId": 0, 
      "type": 0 
    } 
  ], 
  "total": 0 
} 
 
分⻚结果对象«ConvertTransferPageResp»
42.751. Properties
Name
Type
Required
Restrictions
Description
rows
[ConvertTransferPageResp]
false
none
none
total
integer(int64)
false
none
none
_CustodyTransferHistoryResp_
{ 
  "rows": [ 


---

## Page 406

sapi-v7.4.md
2024-05-08
406 / 419
    { 
      "amount": 0, 
      "asset": "string", 
      "clientTranId": "string", 
      "time": "2019-08-24T14:15:22Z", 
      "transferType": "string" 
    } 
  ], 
  "total": 0 
} 
 
分⻚结果对象«CustodyTransferHistoryResp»
42.752. Properties
Name
Type
Required
Restrictions
Description
rows
[CustodyTransferHistoryResp]
false
none
none
total
integer(int64)
false
none
none
_FutureTransferHistoryResp_
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "clientTranId": "string", 
      "status": "CONFIRMED", 
      "timestamp": 0, 
      "tranId": 0, 
      "type": 0 
    } 
  ], 
  "total": 0 
} 
 
分⻚结果对象«FutureTransferHistoryResp»
42.753. Properties
Name
Type
Required
Restrictions
Description
rows
[FutureTransferHistoryResp]
false
none
none
total
integer(int64)
false
none
none
_LedgerTransferPageResp_
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "createTime": "2019-08-24T14:15:22Z", 
      "status": "string", 
      "tranId": 0, 
      "type": 0 
    } 
  ], 
  "total": 0 
} 
 
分⻚结果对象«LedgerTransferPageResp»
42.754. Properties
Name
Type
Required
Restrictions
Description
rows
[LedgerTransferPageResp]
false
none
none


---

## Page 407

sapi-v7.4.md
2024-05-08
407 / 419
Name
Type
Required
Restrictions
Description
total
integer(int64)
false
none
none
_OtcChannelQueryResp_
{ 
  "rows": [ 
    { 
      "completedTime": "string", 
      "inAmount": 0, 
      "inCoin": "string", 
      "outAmount": 0, 
      "outCoin": "string", 
      "quoteId": "string", 
      "side": "string", 
      "status": "string", 
      "symbol": "string" 
    } 
  ], 
  "total": 0 
} 
 
分⻚结果对象«OtcChannelQueryResp»
42.755. Properties
Name
Type
Required
Restrictions
Description
rows
[OtcChannelQueryResp]
false
none
none
total
integer(int64)
false
none
none
_OtcHistoryResp_
{ 
  "rows": [ 
    { 
      "baseCoin": "string", 
      "baseCoinAmount": 0, 
      "direction": "string", 
      "orderId": "string", 
      "quoteCoin": "string", 
      "quoteCoinAmount": 0, 
      "quotePrice": 0, 
      "status": "string", 
      "time": "2019-08-24T14:15:22Z" 
    } 
  ], 
  "total": 0 
} 
 
分⻚结果对象«OtcHistoryResp»
42.756. Properties
Name
Type
Required
Restrictions
Description
rows
[OtcHistoryResp]
false
none
none
total
integer(int64)
false
none
none
_QueryTransferPageResponse_
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "createTime": "2019-08-24T14:15:22Z", 
      "openId": "string", 
      "orderId": "string", 


---

## Page 408

sapi-v7.4.md
2024-05-08
408 / 419
      "status": "string", 
      "tranType": "IN" 
    } 
  ], 
  "total": 0 
} 
 
分⻚结果对象«QueryTransferPageResponse»
42.757. Properties
Name
Type
Required
Restrictions
Description
rows
[QueryTransferPageResponse]
false
none
none
total
integer(int64)
false
none
none
_UserAssetDividendResp_
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "divTime": "2019-08-24T14:15:22Z", 
      "enInfo": "string", 
      "id": 0, 
      "tranId": 0 
    } 
  ], 
  "total": 0 
} 
 
分⻚结果对象«UserAssetDividendResp»
42.758. Properties
Name
Type
Required
Restrictions
Description
rows
[UserAssetDividendResp]
false
none
none
total
integer(int64)
false
none
none
_UserAssetLogResp_
{ 
  "rows": [ 
    { 
      "asset": "string", 
      "delta": 0, 
      "time": "2019-08-24T14:15:22Z", 
      "type": 0 
    } 
  ], 
  "total": 0 
} 
 
分⻚结果对象«UserAssetLogResp»
42.759. Properties
Name
Type
Required
Restrictions
Description
rows
[UserAssetLogResp]
false
none
none
total
integer(int64)
false
none
none
_UserAssetLogV2Resp_


---

## Page 409

sapi-v7.4.md
2024-05-08
409 / 419
{ 
  "rows": [ 
    { 
      "asset": "string", 
      "delta": 0, 
      "enInfo": "string", 
      "free": 0, 
      "freeze": 0, 
      "id": 0, 
      "info": "string", 
      "locked": 0, 
      "time": "2019-08-24T14:15:22Z", 
      "tranId": 0, 
      "type": 0, 
      "withdrawing": 0 
    } 
  ], 
  "total": 0 
} 
 
分⻚结果对象«UserAssetLogV2Resp»
42.760. Properties
Name
Type
Required
Restrictions
Description
rows
[UserAssetLogV2Resp]
false
none
none
total
integer(int64)
false
none
none
_WalletTransferHistoryResp_
{ 
  "rows": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "status": "CONFIRMED", 
      "timestamp": 0, 
      "tranId": 0, 
      "type": "CMFUTURE_FUNDING" 
    } 
  ], 
  "total": 0 
} 
 
分⻚结果对象«WalletTransferHistoryResp»
42.761. Properties
Name
Type
Required
Restrictions
Description
rows
[WalletTransferHistoryResp]
false
none
none
total
integer(int64)
false
none
none
_apiKey_2
{ 
  "rows": [ 
    { 
      "apiName": "string", 
      "apikey": "string", 
      "canFuturesTrade": true, 
      "canMarginLoanRepay": true, 
      "canTrade": true, 
      "canUniversalTransfer": true, 
      "canVanillaOptions": true, 
      "email": "string", 
      "timestamp": 0 
    } 
  ], 
  "total": 0 


---

## Page 410

sapi-v7.4.md
2024-05-08
410 / 419
} 
 
分⻚结果对象«查询⼦账户apiKey»
42.762. Properties
Name
Type
Required
Restrictions
Description
rows
[_apiKey3]
false
none
none
total
integer(int64)
false
none
none
_apiKey
{ 
  "apiKey": "string", 
  "secretKey": "string", 
  "timestamp": 0 
} 
 
创建⼦账户apiKey
42.763. Properties
Name
Type
Required
Restrictions
Description
apiKey
string
false
none
apiKey
secretKey
string
false
none
secretKey
timestamp
integer(int64)
false
none
时间戳
_apiKey2
{} 
 
删除⼦账户apiKey
42.764. Properties
None
_MerchantDetailVo
{ 
  "advConfirmTime": 0, 
  "assetTicketSize": "string", 
  "authentication": true, 
  "bindMobile": true, 
  "chanelInvolved": "string", 
  "emailVerified": true, 
  "firstOrderDays": 0, 
  "idVerified": true, 
  "margin": 0, 
  "marginUnit": "string", 
  "merchantNo": "string", 
  "monthFinishRate": 0, 
  "monthOrderCount": 0, 
  "nickColor": "string", 
  "nickName": "string", 
  "onlineStatus": "string", 
  "orderCount": 0, 
  "registerDays": 0, 
  "userGradeInstanceResp": { 
    "agreementSigned": 0, 
    "emailStatus": 0, 
    "kycStatus": 0, 
    "marginStatus": 0, 
    "mobileStatus": 0, 
    "nickNameStatus": 0, 
    "userGrade": 0 


---

## Page 411

sapi-v7.4.md
2024-05-08
411 / 419
  }, 
  "userKycResp": { 
    "addressStatus": "string", 
    "kycType": "string" 
  }, 
  "userNo": "string", 
  "userStatsResp": { 
    "avgPayTimeOfLatest30day": 0, 
    "avgReleaseTimeOfLatest30day": 0, 
    "completedBuyOrderNum": 0, 
    "completedBuyOrderNumOfLatest30day": 0, 
    "completedBuyOrderTotalBtcAmount": 0, 
    "completedOrderNum": 0, 
    "completedOrderNumOfLatest30day": 0, 
    "completedOrderTotalBtcAmount": 0, 
    "completedOrderTotalBtcAmountOfLatest30day": 0, 
    "completedSellOrderNum": 0, 
    "completedSellOrderNumOfLatest30day": 0, 
    "completedSellOrderTotalBtcAmount": 0, 
    "finishRateLatest30day": 0, 
    "firstOrderDays": 0, 
    "payMethodCount": 0, 
    "registerDays": 0 
  }, 
  "userType": "string" 
} 
 
商户详情MerchantDetailVo
42.765. Properties
Name
Type
Required
Restrictions
Description
advConfirmTime
integer(int32)
false
none
Average release time (seconds)
assetTicketSize
string
false
none
Margin asset decimal precision
authentication
boolean
false
none
If merchant is Authenticated
bindMobile
boolean
false
none
If merchant mobile number bound
chanelInvolved
string
false
none
none
emailVerified
boolean
false
none
If merchant email verified
firstOrderDays
integer(int32)
false
none
none
idVerified
boolean
false
none
If merchant kyc verified
margin
number
false
none
Margin amount
marginUnit
string
false
none
Margin unit, e.g., BNB
merchantNo
string
false
none
Merchant number
monthFinishRate
number
false
none
30-day completion rate
monthOrderCount
integer(int32)
false
none
30-day order count
nickColor
string
false
none
none
nickName
string
false
none
User nickname
onlineStatus
string
false
none
Online/Offline status: (0ÏOffline, 1ÏOnline)
orderCount
integer(int32)
false
none
Total order count
registerDays
integer(int32)
false
none
none
userGradeInstanceResp
UserGradeInstanceResp
false
none
none
userKycResp
UserKycResp
false
none
none
userNo
string
false
none
User number
userStatsResp
UserStatsResp
false
none
none
userType
string
false
none
User type: (user, merchant)
_Ip_Response
{ 
  "apikey": "string", 


---

## Page 412

sapi-v7.4.md
2024-05-08
412 / 419
  "ipList": [ 
    "string" 
  ], 
  "ipRestrict": "string", 
  "subaccountId": "string", 
  "updateTime": 0 
} 
 
⼦账户Ip限制Response
42.766. Properties
Name
Type
Required
Restrictions
Description
apikey
string
false
none
apiKey
ipList
[string]
false
none
限制ip列表
ipRestrict
string
false
none
是否IP限制
subaccountId
string
false
none
⼦账户id
updateTime
integer(int64)
false
none
时间
_margin_Response
{ 
  "tranId": 0 
} 
 
⼦账户margin划转Response
42.767. Properties
Name
Type
Required
Restrictions
Description
tranId
integer(int64)
false
none
事务操作id
_brokersubacount_res
{ 
  "maxMakerCommission": 0, 
  "maxSubAccountQty": 0, 
  "maxTakerCommission": 0, 
  "minMakerCommission": 0, 
  "minTakerCommission": 0, 
  "subAccountQty": 0 
} 
 
更新brokersubacount的res
42.768. Properties
Name
Type
Required
Restrictions
Description
maxMakerCommission
number
false
none
none
maxSubAccountQty
integer(int32)
false
none
none
maxTakerCommission
number
false
none
none
minMakerCommission
number
false
none
none
minTakerCommission
number
false
none
none
subAccountQty
integer(int64)
false
none
none
_broker_
{ 
  "asset": "string", 
  "income": "string", 


---

## Page 413

sapi-v7.4.md
2024-05-08
413 / 419
  "status": 0, 
  "subaccountId": "string", 
  "symbol": "string", 
  "time": 0, 
  "tradeId": 0 
} 
 
查询broker佣⾦明细结果
42.769. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
资产名称
income
string
false
none
佣⾦⾦额
status
integer(int32)
false
none
none
subaccountId
string
false
none
三⽅备注id
symbol
string
false
none
交易产品名称
time
integer(int64)
false
none
交易时间
tradeId
integer(int64)
false
none
交易id
_apiKey3
{ 
  "apiName": "string", 
  "apikey": "string", 
  "canFuturesTrade": true, 
  "canMarginLoanRepay": true, 
  "canTrade": true, 
  "canUniversalTransfer": true, 
  "canVanillaOptions": true, 
  "email": "string", 
  "timestamp": 0 
} 
 
查询⼦账户apiKey
42.770. Properties
Name
Type
Required
Restrictions
Description
apiName
string
false
none
API名称
apikey
string
false
none
apikey
canFuturesTrade
boolean
false
none
canFuturesTrade
canMarginLoanRepay
boolean
false
none
canMarginLoanRepay
canTrade
boolean
false
none
canTrade
canUniversalTransfer
boolean
false
none
canUniversalTransfer
canVanillaOptions
boolean
false
none
canVanillaOptions
email
string
false
none
⼦账户邮箱
timestamp
integer(int64)
false
none
时间戳
_Response
{ 
  "apiAgentCode": "string", 
  "ifNewUser": true, 
  "rebateWorking": true, 
  "referrerId": 0 
} 
 
查询⽤户是否满⾜返佣条件Response


---

## Page 414

sapi-v7.4.md
2024-05-08
414 / 419
42.771. Properties
Name
Type
Required
Restrictions
Description
apiAgentCode
string
false
none
api返佣码
ifNewUser
boolean
false
none
对该推荐码是否为新客 true:新客 false:⽼客
rebateWorking
boolean
false
none
对该推荐码是否满⾜API反佣条件
referrerId
integer(int64)
false
none
推荐⼈ID
_2
{ 
  "appliedAmount": 0, 
  "coin": "string", 
  "platformName": "string", 
  "sourceAddress": "string", 
  "sourceAddressType": 0, 
  "txId": "string", 
  "uploadedMaterialKeys": [ 
    "string" 
  ] 
} 
 
标签币充值找回申请
42.772. Properties
Name
Type
Required
Restrictions
Description
appliedAmount
number
false
none
申请找回⾦额
coin
string
false
none
申请找回币种
platformName
string
false
none
来源平台名称,optinal
sourceAddress
string
false
none
来源地址/期望退款地址,optional
sourceAddressType
integer(int32)
false
none
来源地址类型, 0=个⼈ 1=平台, optinal
txId
string
false
none
充值txId
uploadedMaterialKeys
[string]
false
none
已⾃⾏上传的关联材料key
_Ip_Response2
{ 
  "apiKey": "string", 
  "ip": "string", 
  "subaccountId": "string", 
  "updateTime": 0 
} 
 
添加⼦账户限制Ip Response
42.773. Properties
Name
Type
Required
Restrictions
Description
apiKey
string
false
none
apiKey
ip
string
false
none
本次新添加的ip
subaccountId
string
false
none
⼦账户id
updateTime
integer(int64)
false
none
时间
_Ip_Response3
{ 
  "apiKey": "string", 
  "ip": "string", 
  "updateTime": 0 


---

## Page 415

sapi-v7.4.md
2024-05-08
415 / 419
} 
 
添加账户限制Ip Response
42.774. Properties
Name
Type
Required
Restrictions
Description
apiKey
string
false
none
apiKey
ip
string
false
none
本次新添加的ip
updateTime
integer(int64)
false
none
时间
_3
{ 
  "createTime": "2019-08-24T14:15:22Z", 
  "cryptoCurrency": "string", 
  "fiatCurrency": "string", 
  "obtainAmount": "string", 
  "orderNo": "string", 
  "paymentMethod": "string", 
  "price": "string", 
  "sourceAmount": "string", 
  "status": "string", 
  "totalFee": "string", 
  "updateTime": "2019-08-24T14:15:22Z" 
} 
 
⽤户买卖订单详情
42.775. Properties
Name
Type
Required
Restrictions
Description
createTime
string(date-time)
false
none
订单创建时间
cryptoCurrency
string
false
none
虚拟币token
fiatCurrency
string
false
none
法币token
obtainAmount
string
false
none
虚拟币交易⾦额
orderNo
string
false
none
订单号
paymentMethod
string
false
none
⽀付⽅式
price
string
false
none
价格
sourceAmount
string
false
none
法币交易⾦额
status
string
false
none
状态:Processing, Completed, Failed, Refunded
totalFee
string
false
none
交易⼿续费
updateTime
string(date-time)
false
none
订单更新时间
_4
{ 
  "data": [ 
    { 
      "amount": 0, 
      "asset": "string", 
      "type": 0, 
      "updateTime": "2019-08-24T14:15:22Z" 
    } 
  ], 
  "page": 0, 
  "totalPageNum": 0, 
  "totalRecords": 0 
} 
 


---

## Page 416

sapi-v7.4.md
2024-05-08
416 / 419
⽤户佣⾦收益明细（⽤于税务）返回结果
42.776. Properties
Name
Type
Required
Restrictions
Description
data
[TaxRebateDetailVo]
false
none
none
page
integer(int32)
false
none
none
totalPageNum
integer(int32)
false
none
none
totalRecords
integer(int32)
false
none
none
_5
{ 
  "amount": "string", 
  "createTime": "2019-08-24T14:15:22Z", 
  "fiatCurrency": "string", 
  "indicatedAmount": "string", 
  "method": "string", 
  "orderNo": "string", 
  "status": "string", 
  "totalFee": "string", 
  "updateTime": "2019-08-24T14:15:22Z" 
} 
 
⽤户充提订单详情
42.777. Properties
Name
Type
Required
Restrictions
Description
amount
string
false
none
实际充值/提现⾦额
createTime
string(date-
time)
false
none
订单创建时间
fiatCurrency
string
false
none
法币token
indicatedAmount
string
false
none
实际付款/收款⾦额
method
string
false
none
交易⽅式
orderNo
string
false
none
订单号
status
string
false
none
状态: Processing,Failed,Successful,Finished,Refunding,Refunded,Refund Failed,Order Partial
credit Stopped
totalFee
string
false
none
交易⼿续费
updateTime
string(date-
time)
false
none
订单更新时间
_V3
{ 
  "asset": "string", 
  "btcValuation": 0, 
  "free": 0, 
  "freeze": 0, 
  "ipoable": 0, 
  "locked": 0, 
  "withdrawing": 0 
} 
 
⽤户持仓V3
42.778. Properties
Name
Type
Required
Restrictions
Description
asset
string
false
none
none
btcValuation
number
false
none
btc估值(包含free+freeze+locked+withdrawing)


---

## Page 417

sapi-v7.4.md
2024-05-08
417 / 419
Name
Type
Required
Restrictions
Description
free
number
false
none
none
freeze
number
false
none
none
ipoable
number
false
none
none
locked
number
false
none
none
withdrawing
number
false
none
none
_6
{ 
  "buyerPayedCount": 0, 
  "inAppealCount": 0, 
  "inAppealCountAfterBuyerPaid": 0, 
  "inAppealCountAfterCancelled": 0, 
  "inAppealCountAfterCancelledBySystem": 0, 
  "inAppealCountAfterCompleted": 0, 
  "inProcessCount": 0, 
  "tradingCount": 0, 
  "userId": 0 
} 
 
⽤户订单数量统计
42.779. Properties
Name
Type
Required
Restrictions
Description
buyerPayedCount
integer(int64)
false
none
none
inAppealCount
integer(int64)
false
none
none
inAppealCountAfterBuyerPaid
integer(int64)
false
none
买家已付款后发起申诉的订单数量
inAppealCountAfterCancelled
integer(int64)
false
none
已取消（买家）后发起申诉的订单数量
inAppealCountAfterCancelledBySystem
integer(int64)
false
none
系统（超时）取消后发起申诉的订单数量
inAppealCountAfterCompleted
integer(int64)
false
none
已完成后发起申诉的订单数量
inProcessCount
integer(int64)
false
none
none
tradingCount
integer(int64)
false
none
none
userId
integer(int64)
false
none
none
_url
{ 
  "fileType": 0, 
  "requestType": 0 
} 
 
获取上传材料的预定义url
42.780. Properties
Name
Type
Required
Restrictions
Description
fileType
integer(int32)
false
none
-1: UNKNOWN; 0: MP3; 1: MP4; 2: MOV; 3: RMVB; 4: MKV
requestType
integer(int32)
false
none
找回申请类型: 1=标签币找回, 2=充值未到账找回
_7
{ 
  "complaintAmount": 0, 
  "completedComplaintAmount": 0, 
  "processingComplaintAmount": 0 
} 
 


---

## Page 418

sapi-v7.4.md
2024-05-08
418 / 419
订单申诉数量
42.781. Properties
Name
Type
Required
Restrictions
Description
complaintAmount
integer(int32)
false
none
总的申诉数量
completedComplaintAmount
integer(int32)
false
none
已完成的申诉数量
processingComplaintAmount
integer(int32)
false
none
进⾏中的申诉数量
_Ip_Response4
{ 
  "apiKey": "string", 
  "ipList": [ 
    "string" 
  ], 
  "ipRestrict": "string", 
  "updateTime": 0 
} 
 
账户Ip限制Response
42.782. Properties
Name
Type
Required
Restrictions
Description
apiKey
string
false
none
apiKey
ipList
[string]
false
none
限制ip列表
ipRestrict
string
false
none
是否IP限制
updateTime
integer(int64)
false
none
时间
_field
{ 
  "createTime": "2019-08-24T14:15:22Z", 
  "errorKey": "string", 
  "errorWord": "string", 
  "fieldContentType": "string", 
  "fieldId": "string", 
  "fieldName": "string", 
  "fieldTitle": "string", 
  "fieldTitleKey": "string", 
  "fieldValue": "string", 
  "hintKey": "string", 
  "hintWord": "string", 
  "id": 0, 
  "isCopyable": 0, 
  "isDisplay": 0, 
  "isEncrypt": 0, 
  "isRequired": 0, 
  "lengthLimit": 0, 
  "restrictionType": 0, 
  "sequence": 0, 
  "status": 0, 
  "updateTime": "2019-08-24T14:15:22Z" 
} 
 
配置化field
42.783. Properties
Name
Type
Required
Restrictions
Description
createTime
string(date-time)
false
none
创建时间
errorKey
string
false
none
报错⽂案多语⾔key


---

## Page 419

sapi-v7.4.md
2024-05-08
419 / 419
Name
Type
Required
Restrictions
Description
errorWord
string
false
none
报错⽂案
fieldContentType
string
false
none
field内容类型
fieldId
string
false
none
none
fieldName
string
false
none
none
fieldTitle
string
false
none
none
fieldTitleKey
string
false
none
field标题多语⾔key
fieldValue
string
false
none
字段值
hintKey
string
false
none
提示⽂案多语⾔key
hintWord
string
false
none
提示⽂案
id
integer(int64)
false
none
主键id
isCopyable
integer(int32)
false
none
none
isDisplay
integer(int32)
false
none
是否展示. 0 - Hide, 1 - Public, 2 - Private
isEncrypt
integer(int32)
false
none
是否加密
isRequired
integer(int32)
false
none
是否必须
lengthLimit
integer(int32)
false
none
⻓度限制
restrictionType
integer(int32)
false
none
输⼊限制类型
sequence
integer(int32)
false
none
序列号
status
integer(int32)
false
none
none
updateTime
string(date-time)
false
none
修改时间
