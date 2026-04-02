Техническое задание
на разработку платформы токенизации
объектов интеллектуальной собственности
Проект: веб-платформа для верификации правообладателей, токенизации IP-активов и их размещения на маркетплейсе с расчётами в Solana
Заказчик / продукт	Концепт MVP / Product & Engineering brief
Формат документа	Техническое задание
Версия	v1.0
Дата	31.03.2026

Назначение документа
Документ описывает целевую архитектуру, требования к базе данных, backend и frontend-слоям, интеграциям, сценариям работы пользователей, а также ограничения MVP для платформы токенизации объектов интеллектуальной собственности. Документ предназначен как исходная база для проектирования, декомпозиции задач и подготовки roadmap разработки.

 
1. Цели и границы проекта
•	Создать веб-платформу, на которой правообладатель может зарегистрироваться, пройти идентификацию, подтвердить связь с объектом интеллектуальной собственности и инициировать токенизацию актива.
•	Обеспечить выпуск токенизированного актива в сети Solana после прохождения проверок и внутреннего approval workflow.
•	Предоставить маркетплейс, на котором верифицированные инвесторы могут просматривать активы, проходить onboarding и покупать токены за SOL.
•	Соблюдать принцип: чувствительные действия (токенизация, покупка, листинг, вывод средств) доступны только после обязательных compliance-проверок; KYC может быть необязательным на этапе просмотра и предварительной подачи заявки, но не на этапе выпуска и торговли.
2. Предположения и ограничения
•	Проект стартует как MVP с упором на один тип объектов: патенты США.
•	Проверка патента выполняется через внешние API и реестры USPTO; юридическое решение о допустимости токенизации подтверждается внутренним manual review.
•	Персональные данные, изображения документов и результаты KYC не размещаются on-chain.
•	On-chain слой хранит только необходимые данные о выпуске токена, адресах mint/account и результатах транзакций.
•	Платформа проектируется как permissioned marketplace: выпуск и покупка активов контролируются backend-логикой и compliance-правилами.
3. Роли пользователей и доступ
Роль	Описание	Разрешённые действия
Guest	Неавторизованный посетитель	Просмотр витрины, FAQ, карточек активов в публичной части
User	Зарегистрированный пользователь без одобрения	Профиль, подключение кошелька, черновик заявки на IP, старт KYC
Issuer	Правообладатель / заявитель	Подача IP, загрузка документов, прохождение KYC, запуск токенизации после approval
Investor	Покупатель токенов	KYC, просмотр активов, покупка токенов, управление портфелем
Compliance Officer	Сотрудник проверки	Ручной review KYC/IP, approval/reject, audit log
Admin	Администратор платформы	Управление пользователями, активами, листингом, системными настройками

4. Функциональные блоки платформы
4.1. Identity & Access
Регистрация, авторизация, email verification, роли, управление сессиями, привязка wallet address.
4.2. KYC / Compliance
Запуск и мониторинг KYC-процесса, получение webhook-результатов, sanctions/risk screening, ручной review спорных кейсов.
4.3. IP Verification
Подача patent number, запрос к USPTO API, сопоставление с данными заявителя, проверка supporting documents, решение о допустимости токенизации.
4.4. Asset Management
Создание карточки актива, хранение метаданных, статусов, юридических документов, состава выпуска, параметров токенизации.
4.5. Tokenization
Mint токена в сети Solana, настройка supply, treasury и адресов хранения, привязка on-chain сущностей к off-chain записям актива.
4.6. Marketplace
Листинг активов, размещение офферов, покупка токенов за SOL, контроль допустимости сделки и пост-обработка settlement.
4.7. Admin & Audit
Панели управления, отчётность, хронология действий, журнал ошибок, экспорт данных и мониторинг интеграций.
5. Основные пользовательские сценарии
5.1. Сценарий правообладателя (issuer)
1.	Регистрация и подтверждение email.
2.	Заполнение профиля и привязка кошелька.
3.	Подача patent number и базовых данных по объекту.
4.	Предварительная автоматическая проверка по USPTO.
5.	Прохождение KYC и загрузка supporting documents. (optioanal)
6.	Ручной review специалистом compliance/legal.
7.	Одобрение заявки и выпуск токена в Solana.
8.	Публикация актива в маркетплейсе.
5.2. Сценарий инвестора
9.	Регистрация и подтверждение email.
10.	Просмотр витрины активов и карточек размещений.
11.	Прохождение KYC и compliance screening перед первой покупкой. (optional)
12.	Подключение кошелька Solana.
13.	Покупка токенов за SOL.
14.	Отображение позиций в портфеле и истории операций.
5.3. Сценарий compliance officer (optional)
15.	Получение очереди кейсов KYC/IP review.
16.	Просмотр досье пользователя и объекта IP.
17.	Вынесение решения: approve / reject / request more data.
18.	Формирование причин отказа и комментариев в audit log.
6. Архитектура базы данных
Рекомендуемая СУБД: PostgreSQL. Доступ к данным — через ORM/Query Builder (Prisma или Drizzle) с разграничением read/write операций и поддержкой миграций. Для документов и вложений используется отдельное объектное хранилище (например, S3-compatible storage).
Принцип проектирования БД
Нормализованные сущности отвечают за пользователей, проверки, объекты IP, токенизации, листинги и сделки. PII и документы не хранятся в блокчейне; в базе сохраняются статусы, связи, результаты проверок, системные идентификаторы и ссылки на защищённые файлы.

6.1. Ключевые таблицы
Таблица	Назначение	Ключевые поля
users	Учетные записи	id, email, password_hash, role, status, wallet_address
profiles	Анкетные данные пользователя	user_id, legal_name, dob, country, address
kyc_cases	Проверки личности	id, user_id, provider, provider_case_id, status, review_result
sanctions_checks	Скрининг по рискам	id, user_id, status, flags, checked_at
ip_claims	Заявки на IP	id, issuer_user_id, patent_number, claimed_owner_name, status
ip_documents	Документы по IP-кейсу	id, ip_claim_id, file_url, doc_type, uploaded_at
ip_reviews	Результаты ручной проверки	id, ip_claim_id, reviewer_id, decision, notes
assets	Карточки токенизируемых активов	id, ip_claim_id, title, status, legal_structure
token_issuances	On-chain выпуск	id, asset_id, mint_address, network, total_supply, decimals
listings	Размещения на маркетплейсе	id, asset_id, listing_status, price_model, start_at
orders	Заявки на покупку	id, listing_id, buyer_user_id, qty, amount_sol, status
trades	Исполненные сделки	id, order_id, tx_signature, settled_at, settlement_status
wallet_links	Связь аккаунта и кошельков	id, user_id, wallet_address, is_primary
audit_logs	История действий	id, actor_id, action, entity_type, entity_id, payload
webhook_events	Сырые входящие события интеграций	id, source, external_id, status, payload

6.2. Статусы доменных сущностей
Сущность	Статусы
users.status	active, suspended, blocked, pending_email_verification
kyc_cases.status	not_started, pending, needs_input, manual_review, approved, rejected, expired
ip_claims.status	draft, submitted, prechecked, awaiting_kyc, under_review, approved, rejected
assets.status	draft, approved_for_tokenization, tokenized, listed, paused, archived
listings.listing_status	draft, active, paused, closed, cancelled
orders.status	created, blocked_kyc_required, pending_compliance, approved, paid, failed, cancelled
trades.settlement_status	pending, settled, failed, reversed

6.3. Логические связи
•	Один пользователь может иметь одну запись users, один профиль profiles и несколько кошельков в wallet_links.
•	Один пользователь может иметь несколько KYC-кейсов (повторные проверки), но только один активный кейс со статусом pending/manual_review.
•	Одна заявка ip_claims относится к одному issuer, но может иметь несколько supporting documents и одну или несколько записей ручной проверки.
•	Один актив assets создаётся на базе одобренной заявки ip_claims и имеет максимум один актуальный token_issuance на MVP-этапе.
•	Один listing относится к одному asset; один listing может порождать множество orders и trades.
7. Архитектура backend
Рекомендуемая реализация: Next.js backend (Route Handlers) на старте или выделенный Node.js/NestJS backend при росте команды. Архитектура должна быть модульной, со слоями API → service → repository/integration. Интеграции с KYC, USPTO и Solana выносятся в отдельные адаптеры.
Модуль	Ответственность	Основные эндпоинты / методы
auth	Регистрация, login, session/JWT, роли	/api/auth/register, /login, /logout, /me
users	Профиль, wallet linking, настройки	/api/users/profile, /wallets/link
kyc	Старт KYC, статусы, webhook, retry	/api/kyc/start, /status, /webhook
compliance	Санкции, eligibility, risk flags	checkUserEligibility(), screenUser()
patents	Запросы в USPTO, pre-check, нормализация данных	/api/patents/precheck, /verify
ip-claims	Подача и review кейсов по IP	/api/ip-claims, /review, /documents
assets	Карточки актива, статусный workflow	/api/assets, /assets/{id}
tokenization	Подготовка и mint в Solana	/api/tokenize/mint, /issuances/{id}
marketplace	Листинги, офферы, исполнение ордеров	/api/listings, /orders, /trades
audit	Логи и наблюдаемость	/api/admin/audit, writeAuditLog()

7.1. Внутренние backend-слои
•	API Layer: валидация запросов, авторизация, формирование DTO.
•	Service Layer: бизнес-логика, orchestration процессов KYC/IP verification/tokenization.
•	Repository Layer: работа с PostgreSQL и объектным хранилищем.
•	Integration Layer: адаптеры KYC-provider, USPTO API, Solana RPC, email/notification сервисы.
•	Job/Queue Layer: обработка webhook, повторные запросы, retry и фоновые операции.
7.2. Очереди и фоновые процессы
•	Обработка входящих webhook KYC-провайдера и запись в webhook_events.
•	Повторная синхронизация статуса кейсов при временных ошибках сторонних API.
•	Проверка патентов и enrichment данных из USPTO.
•	Подтверждение on-chain транзакций и reconciliation по mint/trade операциям.
•	Рассылка уведомлений пользователям о статусе проверки и состоянии сделки.
8. Архитектура frontend
Рекомендуемая реализация: Next.js App Router на JSX, клиентские компоненты только для интерактивных сценариев (wallet connect, формы, status polling), серверные компоненты — для статических и полу-статических представлений. UI должен быть разделён на страницы, переиспользуемые компоненты и domain-specific hooks/services.
Слой	Содержимое	Примеры
app/	Маршруты и layout	auth/, kyc/, issuer/, marketplace/, portfolio/
components/	Переиспользуемый UI	ConnectWalletButton, AssetCard, KycStatusBadge
hooks/	Клиентская доменная логика	useKycStatus, useWalletAccount, useAssets
lib/	SDK и утилиты	solana/client.js, patents/api.js, validators.js
services/	Сценарии для данных	asset.service.js, tokenization.service.js
schemas/	Валидация форм и DTO	auth.schema.js, kyc.schema.js, order.schema.js

8.1. Рекомендуемая структура каталогов frontend
src/
  app/
    auth/ login/ register/
    kyc/ issuer/ marketplace/ portfolio/ admin/
    api/
  components/
    ui/ wallet/ kyc/ issuer/ marketplace/
  hooks/
  lib/
    solana/ patents/ auth/ compliance/
  services/
  schemas/

8.2. Ключевые frontend-экраны
Экран	Назначение	Ключевые элементы
Landing	Публичная витрина	hero, преимущества, FAQ, CTA регистрации
Register/Login	Онбординг пользователя	email, password/magic link, accept TOS
KYC	Прохождение верификации	статус, start verification, retry, explainers
Issuer Dashboard	Рабочая зона правообладателя	список кейсов, статусы, документы, CTA tokenize
Submit IP	Подача патента	номер патента, данные владельца, upload supporting docs
Marketplace	Список активов	фильтры, карточки активов, статусы размещения
Asset Page	Карточка размещения	описание, метаданные, цена, кнопка Buy
Portfolio	Активы инвестора	балансы, история сделок, tx статусы
Admin/Review	Панель внутреннего review	очереди кейсов, approve/reject, audit

9. API-контракты уровня MVP
Метод	Эндпоинт	Назначение
POST	/api/auth/register	Регистрация пользователя
POST	/api/auth/login	Авторизация
GET	/api/auth/me	Данные текущего пользователя
POST	/api/kyc/start	Создание KYC кейса
GET	/api/kyc/status	Получение статуса KYC
POST	/api/kyc/webhook	Входящий webhook от провайдера
POST	/api/patents/precheck	Предварительная проверка patent number
POST	/api/ip-claims	Создание заявки на IP
POST	/api/ip-claims/{id}/documents	Загрузка supporting documents
POST	/api/ip-claims/{id}/review	Решение по кейсу
POST	/api/assets	Создание карточки актива
POST	/api/tokenize/mint	Запуск токенизации
GET	/api/listings	Список размещений
POST	/api/orders	Создание ордера на покупку
POST	/api/trades/settle	Подтверждение исполнения сделки

9.1. Пример бизнес-правил API
•	Создание IP-кейса доступно зарегистрированному пользователю; токенизация — только при approved KYC и approved IP review.
•	Создание ордера на покупку доступно только пользователю с approved KYC и положительным compliance screening.
•	Webhook-эндпоинты должны проходить проверку подписи и сохранять сырое событие в webhook_events.
•	Все изменения статусов критичных сущностей логируются в audit_logs.
10. Интеграции и внешние системы
Интеграция	Назначение	Примечание
KYC Provider	Идентификация, документ, liveness, decision	Hosted flow/SDK + webhook
USPTO API	Проверка патента и данных о праве	pre-check + enrichment + manual review
Solana RPC	On-chain операции	devnet для MVP, mainnet после hardening
Object Storage	Хранение документов	S3-compatible, private bucket
Email/Notifications	Уведомления	статусы KYC/IP/trade
Monitoring/Logging	Наблюдаемость	ошибки, latency, webhook failures

11. Нефункциональные требования и безопасность
•	PII хранится только в защищённой базе/хранилище; доступ ограничивается по ролям.
•	Пароли хранятся только в виде secure hash.
•	Доступ к административным и review-маршрутам защищён RBAC и audit trail.
•	Внешние webhooks проверяются по подписи и идемпотентности.
•	Ошибки интеграций не должны приводить к потере данных; обязательна очередь повторов и dead-letter обработка.
•	On-chain приватные ключи сервиса не хранятся в исходном коде; используются secrets manager / защищённые env.
•	Все критичные операции (approve, mint, settle, reject) логируются в audit_logs.
12. Рекомендуемый состав MVP
19.	Identity: регистрация, login, email verification, роли.
20.	KYC: интеграция с одним провайдером, статусы и webhook.
21.	IP: подача patent number, pre-check по USPTO, ручной review.
22.	Assets: карточка актива и статусный workflow.
23.	Tokenization: выпуск токена в Solana devnet.
24.	Marketplace: витрина активов и покупка токена за SOL в упрощённом сценарии.
25.	Admin: review-панель для одобрения кейсов и журнал событий.
13. Открытые вопросы для уточнения до старта разработки
•	Какова юридическая модель токенизированного актива: доля владения, право на доход, лицензионное требование или иной формат?
•	Какой KYC-провайдер выбирается для MVP и какие страны/типы документов должны поддерживаться?
•	Какая модель secondary market допустима на старте: фиксированная цена, офферная модель или order book?
•	Какой уровень transfer restrictions нужен для токенов на этапе MVP?
•	Требуется ли поддержка компаний (KYB) в первом релизе или только физических лиц?
•	Нужна ли интеграция с дополнительными источниками права/ownership кроме USPTO?
Итоговая рекомендация
Начинать проект следует как compliance-first платформу: off-chain верификация, KYC и review составляют источник истины, а on-chain слой Solana используется для controlled issuance и расчётов. Для MVP рекомендуется ограничить scope одним типом IP, одним KYC-провайдером, одним сценарием токенизации и упрощённым маркетплейсом.

IPChain FastAPI Backend Design:
Authentication and Patent
Veri cation Module
Scope
This document de nes the backend design for the FastAPI service that
covers only authentication, basic identity, and patent veri cation
work ows for IPChain MVP. The service scope includes
email/password authentication, JWT-based sessions, basic user
identity records, USPTO patent pre-check, creation and review of IP
claims, and upload of supporting patent documents. Tokenization,
Solana interaction, marketplace operations, orders, trades,
settlement, wallet authentication, and wallet linking are explicitly out
of scope for this service.[1][2]
The authentication scope includes user registration, login, logout if
refresh sessions are used, current-user retrieval through
GET
/api/auth/me, secure password hashing, and optional email
veri cation and password reset support because identity and access
requirements in the speci cation mention email veri cation as part
of the platform identity layer.[2]
The user and pro le scope is intentionally minimal and supports only
the data required for authentication, role-based access, pro le
display, and patent-claim ownership. The patent scope includes
USPTO pre-check, enrichment of patent metadata, creation of IP
claims, listing claims with lters, viewing claim details, uploading
supporting documents, and admin or compliance review decisions
with outcomes approve, reject, or request more data.[1][2]
Endpoints
Auth
M
et
ho
d
Path Purpose
Aut
h /
Role
Reques
t Response
PO
ST
/api/aut
h/regist
er
Register
user with
email and
password
No Register
payload
Auth user
or token
payload [1]
[2]
PO
ST
/api/aut
h/login
Login with
email and
password
No Login
payload
Access
token,
optional
refresh
token, user
payload [1]
[2]
PO
ST
/api/aut
h/logou
t
Invalidate
refresh
session if
refresh
model is
enabled
JWT
requ
ired
Optiona
l
refresh/
session
identi e
r
Simple
success
payload [2]
GE
T
/api/aut
h/me
Return
current
authenticat
ed user
JWT
requ
ired
None
Current
user pro le
and role
payload [1]
[2]
PO
ST
/api/aut
h/refres
h
Issue new
access
token from
refresh
token
Refr
esh
requ
ired
Refresh
payload
Token
payload [2]
PO
ST
/api/aut
h/verify-email
Con rm
email
ownership
if email
No Veri ca
tion
token
payload
Veri cation
result [2]
M
et
ho
d
Path Purpose
Aut
h /
Role
Reques
t Response
veri cation
is enabled
PO
ST
/api/aut
h/pass
word
reset/re
quest
Start
password
reset ow
No Email
payload
Simple
success
payload [2]
PO
ST
/api/aut
h/pass
word
reset/co
n rm
Set new
password
by reset
token
No
Reset
token
and
new
passwo
rd
Simple
success
payload [2]
POST /api/auth/register creates a new user record, stores a secure
password hash, initializes a minimal pro le if needed, and either
returns tokens immediately or requires email veri cation rst,
depending on the selected MVP policy.[2]
POST /api/auth/login validates credentials, checks that the user status
allows access, and issues the session token set. Successful and failed
login attempts must be written to audit logs because the speci cation
requires audit coverage for identity and admin-sensitive actions.[2]
GET /api/auth/me exists in the frontend and backend API map and
must return the current identity payload required by the UI, including
role and status. It may also include read-only KYC status for frontend
gating, but this service must not implement KYC work ows itself.[1]
[2]
Users and Pro les
Me
tho
d
GE
T
PUT
Path
/api/use
rs/me/p
ro le
/api/use
rs/me/p
ro le
Purpose
Read
current
pro le
Update
minimal
pro le
elds
Auth
/ Role
JWT
requi
red
Request Response
None
Pro le
payload
[2]
JWT
requi
red
GE
T
/api/use
rs/me/r
oles
Return role
and status
snapshot
JWT
requi
red
Pro le
update
payload
None
Pro le
payload
[2]
Role and
status
payload
[2]
Only a minimal pro le API is needed for this service because the
assignment is limited to auth, role handling, and patent-claim
ownership. Full user administration is not required in this module
design.[2]
Patents and IP-claims
M
et
ho
d
Path Purpose Auth /
Role
Requ
est
Respon
se
PO
ST
/api/pa
tents/p
rechec
k
Proxy and
normalize
USPTO or
external
patent API
lookup
JWT
required,
user or
issuer or
admin
Patent
pre
check
paylo
ad
Patent
pre
check
result
[1][2]
PO
ST
/api/ip
claims
Create a new
IP-claim for
a patent
JWT
required,
issuer or
allowed
equivalen
t
IP
claim
create
paylo
ad
IP-claim
payload
[1][2]
GE
T
/api/ip
claims
List IP
claims with
lters
JWT
required
Query
lters
List of
IP
claims
[1][2]
GE
T
/api/ip
claims/
{id}
Return claim
details
JWT
required,
owner or
reviewer
role
None
IP-claim
payload
[1][2]
PO
ST
/api/ip
claims/
{id}/do
cumen
ts
Upload
supporting
claim
documents
JWT
required,
owner
Multip
art
form
data
Uploade
d
docume
nt
payload
[1][2]
M
et
ho
d
PO
ST
Path
/api/ip
claims/
{id}/re
view
Purpose
Apply admin
review
decision
Auth /
Role
JWT
required,
admin or
complianc
e
Requ
est
Revie
w
decisi
on
paylo
ad
Respon
se
Updated
IP-claim
payload
[1][2]
POST /api/patents/precheck must provide a normalized response
contract even if external provider responses vary. The frontend
speci cation expects pre-check outcomes including found, not found,
partial match, and external API unavailable states together with title,
owner, and metadata enrichment when available.[1]
POST /api/ip-claims creates the claim record linked to the issuer user
and stores the patent number, claimed owner name, user-entered
data, and any enrichment data from pre-check.
GET /api/ip-claims
must support status ltering because issuer dashboards and admin
review queues both rely on status-based lists.[1][2]
POST /api/ip-claims/{id}/review records the reviewer decision and
review notes and moves the claim to the appropriate resulting status.
The review ow must support approve, reject, and request more data
because those actions are explicitly de ned in the admin review
queue requirements.[1][2]
Schemas
Authentication DTOs
The service should de ne request and response schemas for
registration, login, current user, and token issue.
RegisterRequest
should contain email, password, con rm password, and optional
minimal pro le elds such as legal name and country if onboarding
requires them.
LoginRequest should contain email and password.
AuthUserResponse should return user identi er, email, role, status,
optional KYC status as a read-only UI eld, and an embedded minimal
pro le summary.
TokenResponse should return access token,
optional refresh token, token type, expiry metadata, and the current
user payload.[1][2]
Patent Pre-check DTOs
PatentPrecheckRequest should contain patent number as the
required eld and optional context elds such as jurisdiction and
claimed owner name.
PatentPrecheckResponse should return a
normalized status value from the set found, not found, partial, or
error, together with patent number, title, owner, metadata, source
identi er, a boolean prechecked ag, and a human-readable message
when needed.[1]
IP-claim DTOs
CreateIpClaimRequest should include patent number, optional patent
title, claimed owner name, optional description, optional jurisdiction,
and an optional pre-check snapshot or reference when the claim is
created after an enrichment step.
IpClaimResponse should return
claim identi er, issuer user identi er, patent number, patent title if
known, claimed owner name, description, jurisdiction, claim status,
prechecked ag, patent metadata, and timestamps.[1][2]
IpClaimStatus should be de ned using the statuses present in the
speci cation for IP-claims: draft, submitted, prechecked, awaitingkyc,
underreview, approved, and rejected. Even though KYC logic is
outside this module, the status value awaitingkyc may still appear if
another external service in uences claim progression.[2]
Review and Document DTOs
IpClaimReviewRequest should contain a decision eld with values
approve, reject, or request more data, plus optional review notes.
UploadDocumentResponse should return uploaded document
identi er, related claim identi er, le URL or storage key exposure
value, document type, and upload timestamp.[1][2]
JWT and Session Model
The access token should include only the claims needed for
authentication and authorization decisions in this service. The
recommended claim set is
and jti.
sub,
user_id,
email,
role,
status,
iat,
exp,
kyc_status may be added only as an informational UI eld if
the frontend requires it for display or gating, but it must not
introduce KYC work ow logic into this FastAPI module.[1][2]
The preferred session model is short-lived access tokens with longer
lived refresh tokens because the speci cation mentions JWT sessions
and logout behavior. A practical model is an access token lifetime of
about 15 to 30 minutes and a refresh token lifetime of 7 to 30 days,
with refresh tokens stored server-side in hashed form or represented
by a revocable session store so that logout can actively invalidate
sessions.[2]
If the implementation intentionally avoids refresh tokens in the MVP,
then
POST /api/auth/logout can be omitted or reduced to a client-side
token discard pattern, but that weakens server-side session
revocation. For production-ready behavior, refresh support is
preferable.[2]
The FastAPI authorization layer should provide a current-user
dependency that decodes the bearer token, resolves the user from the
database, and rejects inactive or blocked users. A separate role-guard
dependency should enforce route-level access rules such as issuer
only claim creation and admin or compliance-only review actions.[1]
[2]
FastAPI Structure
The service should be organized into API, service, repository, model,
schema, and core security layers because the backend architecture in
the speci cation explicitly separates API layer, service layer,
repository layer, and integration layer. This structure keeps
controllers thin, centralizes business rules, and isolates external
USPTO access into a dedicated integration client.[2]
Recommended package structure:
app/api/v1/auth.py
app/api/v1/users.py
app/api/v1/patents.py
app/api/v1/ip_claims.py
app/api/v1/admin_reviews.py
app/models/ for ORM entities
app/schemas/ for Pydantic DTOs
app/services/auth_service.py
app/services/patent_service.py
app/services/ip_claims_service.py
app/services/review_service.py
app/repositories/user_repo.py
app/repositories/ip_claim_repo.py
app/repositories/document_repo.py
app/repositories/review_repo.py
app/repositories/audit_log_repo.py
app/core/security.py
app/core/con g.py
app/core/rate_limit.py
[2]
This structure cleanly isolates authentication concerns from patent
lookup concerns and keeps document handling separate from review
orchestration. It also matches the domain modules and layered
backend approach described in the speci cation without introducing
out-of-scope tokenization or marketplace components.[2]
DB Layer
The database layer should use PostgreSQL with an ORM or query
builder, and only the tables relevant to this scope should be included
in the FastAPI module. The relevant tables are users, pro les,
ipclaims, ipdocuments, ipreviews, and auditlogs.
webhookevents
must not be part of this module because KYC webhooks and similar
external callbacks are outside the requested scope.[2]
users maps to the authentication identity record and should contain
at least email, password hash, role, and status.
pro les maps to the
user pro le extension and should contain at least legal name and
country if required for patent work ows.
ipclaims stores the
ownership claim against a patent number and must include issuer
user identi er, patent number, claimed owner name, status, and
enriched pre-check elds.
ipdocuments stores document references
linked to a claim.
ipreviews stores reviewer decisions, notes, and
reviewer identity.
auditlogs stores auditable events such as login
attempts, claim creation, and review actions.[2]
The table mapping should remain close to the names and semantics
used in the speci cation to minimize mismatch with the broader
platform architecture. Additional internal columns such as
timestamps, normalized patent metadata, pre-check status elds, and
soft-delete markers may be added if they do not change the core
domain model.[2]
Patent Veri cation
The patent veri cation endpoint should call an external USPTO or
equivalent patent API through a dedicated service client. The
endpoint itself should not contain business logic beyond validation
and response forwarding. The patent service should validate and
normalize the patent number, call the upstream provider, handle
timeouts and provider errors, and convert provider-speci c payloads
into a stable internal result contract.[1][2]
The external result should be mapped into four normalized
outcomes.
found means the patent was found with a su ciently
con dent match and usable title or ownership metadata.
partial
means the patent data exists but the result is incomplete, ambiguous,
or mismatched enough to require manual review.
the patent record was not found.
not_found means
error means the provider failed,
timed out, or returned an unusable response.[1]
After a successful or partially successful pre-check, the claim ow
should preserve enriched data on the IP-claim record. The saved
elds should include a prechecked ag, enriched patent title, external
owner name if returned, structured provider metadata, normalized
pre-check status, source identi er, and check timestamp. This allows
the admin review queue to use the pre-check output later without
making the frontend responsible for long-term state.[1][2]
Security
Passwords must be stored only as secure hashes, never in plaintext,
and the speci cation explicitly calls for secure hashing in the identity
layer. A strong password hashing algorithm such as bcrypt or
Argon2id is appropriate for this module. Password policy should
enforce a minimum length, reasonable maximum length, and basic
password con rmation at registration.[2]
JWT signing should use a secure algorithm and a secret or keypair
stored only in environment variables or a secrets manager. The secret
must not be embedded in source code or con guration committed to
the repository.[2]
Rate limiting should be applied at minimum to login and patent pre
check endpoints. Login rate limiting reduces brute-force risk, while
patent pre-check rate limiting protects both the FastAPI service and
the external patent provider from abuse or accidental load spikes.[1]
[2]
Input validation should normalize and validate patent number
format, email format, password length, document types, and le size.
Uploaded les should be stored in private object storage and
represented in the database by document metadata and storage
reference rather than raw le content.[1][2]
Audit logging is required for successful and failed login events,
creation of IP-claims, and claim review outcomes including approve,
reject, and request more data. Audit records should include actor
identity, action name, target entity type, target entity identi er, and a
JSON payload with operational context such as previous status, new
status, IP address, or failure reason where appropriate.[1][2]
Assumptions
This design assumes that Solana, tokenization, marketplace
operations, orders, trades, settlement, wallet authentication, and
wallet linking are implemented by other services and must not
appear in this FastAPI module. This separation follows both the
assignment constraints and the broader architecture in the platform
speci cation.[1][2]
This design assumes that KYC, sanctions screening, and webhooks are
external dependencies. The auth or patent module may consume
external user status information for display or gating, but it does not
expose KYC endpoints and does not own webhook processing.[2]
This design assumes that admin and compliance roles may both
participate in claim review because the speci cations reference
admin review queues and optional compliance o cer review
responsibilities. If the MVP is simpli ed further, review authority can
be restricted to admin only without changing the rest of the module
structure.[1][2]

IPChain MVP Canonical DB
Schema Refactor
This document packages the canonical IPChain MVP database
refactor into a PDF-ready report based on the generated Prisma
schema, SQL migration, and di summary artifacts.
Deliverables
The refactor includes a complete
schema.prisma implementing all
canonical tables, relations, enum lifecycles, FK names, JSONB elds,
and UTC timestamps required by the ТЗ.
It also includes a PostgreSQL migration le with explicit enum
creation, table DDL, indexes, unique constraints, and foreign keys
aligned to the same canonical speci cation.
A separate di summary records that this was generated as a
green eld canonical schema because no legacy schema was provided
in the request payload.
Canonical Coverage
The generated schema de nes the following tables exactly as
required by the ТЗ map:
ipclaims,
users,
ipdocuments,
pro les,
ipreviews,
kyccases,
assets,
orders,
trades,
walletlinks,
sanctionschecks,
tokenissuances,
auditlogs, and
listings,
webhookevents.
users.status,
All lifecycle enums were normalized to canonical values only,
including
users.role,
assets.status,
kyccases.status,
listings.listingstatus,
orders.status,
trades.settlementstatus, and
ipreviews.decision.
ipclaims.status,
All foreign-key columns follow the required naming convention from
the speci cation, such as
buyeruserid,
userid,
ipclaimid,
issueruserid, and
assetid,
listingid,
orderid,
reviewerid.
Compliance Decisions
The schema marks
auditlogs.payload and
webhookevents.payload as
JSONB in both Prisma and SQL, and the same treatment is applied to
other structured metadata elds such as
patentmetadata, and
pricemodel.
PII-sensitive elds such as
reviewresult,
ags,
email,
passwordhash,
legalname,
dob, and
address are explicitly annotated so they are not surfaced unmasked
in
tokenissuances or
auditlogs.payload.
All tables were given UTC-compatible timestamp columns using
created_at,
updated_at, or domain event timestamps like
checkedat,
startat, and
uploadedat,
settledat, with PostgreSQL
TIMESTAMPTZ in
the migration output.
Di Summary
Tables renamed: none, because the output was generated from
scratch without a source schema to compare against.
Columns renamed: none, for the same reason; the result is a
canonical baseline rather than an in-place patch.
Enums changed: not applicable against a prior schema, but the
generated les de ne nine canonical enums with only approved
values.
Columns agged as
NOT IN SPEC: none, because no extra legacy
columns were present in the generated baseline.
Columns added: UTC audit timestamps were added broadly across
tables to satisfy the timestamp rule while preserving the canonical
business elds de ned by the ТЗ.
Attached Artifacts
Prisma schema artifact.
SQL migration artifact.
Di summary artifact.

# IPChain MVP Canonical DB Schema Refactor
This document packages the canonical IPChain MVP database refactor into a PDF-ready report
based on the generated Prisma schema, SQL migration, diff summary, and an ER diagram.
Deliverables
The refactor includes a complete
schema.prisma implementing all canonical tables, relations,
enum lifecycles, FK names, JSONB fields, and UTC timestamps required by the
ТЗ
.
It also includes a PostgreSQL migration file with explicit enum creation, table DDL, indexes,
unique constraints, and foreign keys aligned to the same canonical specification.
A separate diff summary records that this was generated as a greenfield canonical schema
because no legacy schema was provided in the request payload.
Canonical Coverage
The generated schema defines the following tables exactly as required by the
ТЗ
 map:
profiles,
kyccases,
sanctionschecks,
listings,
orders,
ipclaims,
ipdocuments,
trades,
walletlinks,
auditlogs, and
All lifecycle enums were normalized to canonical values only, including
users.role,
kyccases.status,
ipclaims.status,
assets.status,
orders.status,
trades.settlementstatus, and
ipreviews.decision.
users,
ipreviews,
assets,
tokenissuances,
webhookevents.
users.status,
listings.listingstatus,
All foreign-key columns follow the required naming convention from the specification, such as
userid,
ipclaimid,
assetid,
listingid,
orderid,
buyeruserid,
Graphical DB Scheme (Mermaid ER)
issueruserid, and
reviewerid.
The following Mermaid ER diagram represents the canonical relational model and can be
rendered to SVG/PNG in your PDF toolchain.
erDiagram
users ||--|| profiles : has
users ||--o{ kyccases : has
users ||--o{ sanctionschecks : has
users ||--o{ ipclaims : issues
users ||--o{ ipreviews : reviews
users ||--o{ orders : places
users ||--o{ walletlinks : owns
users ||--o{ auditlogs : acts_in
  ipclaims ||--o{ ipdocuments : has
  ipclaims ||--o{ ipreviews : has
  ipclaims ||--o{ assets : backs
  assets ||--o{ tokenissuances : tokenized_by
  assets ||--o{ listings : listed_as
  listings ||--o{ orders : has
  orders ||--o{ trades : settles
  orders }o--|| users : buyer
  ipclaims }o--|| users : issuer
  ipreviews }o--|| users : reviewer
  kyccases }o--|| users : subject
  sanctionschecks }o--|| users : subject
  walletlinks }o--|| users : owner
  auditlogs }o--|| users : actor
  users {
    uuid id
    string email
    string passwordhash
    string role
    string status
    string walletaddress
  }
  profiles {
    uuid userid
    string legalname
    date dob
    string country
    string address
  }
  kyccases {
    uuid id
    uuid userid
    string provider
    string providercaseid
    string status
    jsonb reviewresult
  }
  sanctionschecks {
    uuid id
    uuid userid
    string status
    jsonb flags
    timestamptz checkedat
  }
  ipclaims {
    uuid id
    uuid issueruserid
    string patentnumber
    string claimedownername
    string status
    string patcharttitle
    string patchartowner
    string precheckstatus
    string precheckflag
    string sourceid
    timestamptz checkedat
    jsonb patentmetadata
  }
  ipdocuments {
    uuid id
    uuid ipclaimid
    string fileurl
    string doctype
    timestamptz uploadedat
  }
  ipreviews {
    uuid id
    uuid ipclaimid
    uuid reviewerid
    string decision
    string notes
  }
  assets {
    uuid id
    uuid ipclaimid
    string title
    string status
    string legalstructure
  }
  tokenissuances {
    uuid id
    uuid assetid
    string mintaddress
    string network
    numeric totalsupply
    int decimals
  }
  listings {
    uuid id
    uuid assetid
    string listingstatus
    jsonb pricemodel
    timestamptz startat
  }
  orders {
    uuid id
    uuid listingid
    uuid buyeruserid
    numeric qty
    numeric amountsol
    string status
  }
  trades {
    uuid id
    uuid orderid
    string txsignature
    timestamptz settledat
    string settlementstatus
}
walletlinks {
uuid id
uuid userid
string walletaddress
bool isprimary
}
auditlogs {
uuid id
uuid actorid
string action
string entitytype
string entityid
jsonb payload
}
webhookevents {
uuid id
string source
string externalid
string status
jsonb payload
}
Compliance Decisions
The schema marks
auditlogs.payload and
webhookevents.payload as JSONB in both Prisma and
SQL, and the same treatment is applied to other structured metadata fields such as
reviewresult,
flags,
patentmetadata, and
PII-sensitive fields such as
pricemodel.
email,
passwordhash,
legalname,
dob, and
address are explicitly
annotated so they are not surfaced unmasked in
tokenissuances or
auditlogs.payload.
All tables were given UTC-compatible timestamp columns using
created_at,
updated_at, or
domain event timestamps like
uploadedat,
checkedat,
TIMESTAMPTZ in the migration output.
Diff Summary
startat, and
settledat, with PostgreSQL
Tables renamed: none, because the output was generated from scratch without a source schema
to compare against.
Columns renamed: none, for the same reason; the result is a canonical baseline rather than an
in-place patch.
Enums changed: not applicable against a prior schema, but the generated files define nine
canonical enums with only approved values.
Columns flagged as
NOT IN SPEC: none, because no extra legacy columns were present in the
generated baseline.
Columns added: UTC audit timestamps were added broadly across tables to satisfy the
timestamp rule while preserving the canonical business fields defined by the
ТЗ
.
Attached Artifacts
Prisma schema artifact.
SQL migration artifact.
Diff summary artifact.
