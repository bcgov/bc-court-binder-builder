# CSO Account Setup, Log On and E-Filing (guided help)

How to help a person get from "I have a finished binder" to "it is submitted on Court Services Online (CSO)". This reference is for agents and for the desktop app's **File with CSO** screen.

**Verified on 2026-11-01** against the public CSO pages, the CSO registration guide (PDF), the repository's copy of the April 2026 CSO guide ([cso_application_record_guide_april2026.md](cso_application_record_guide_april2026.md)), the CSO eFile "Getting Started" help text and screenshots supplied by the project owner. Addresses are kept in [cso_links.json](cso_links.json); use that file, do not hard-code URLs elsewhere. CSO can change; items marked *not verified* have not been confirmed.

## What you may and may not do

You **guide**. The person does every step on CSO's own site.

- Never type, request, store or repeat a password, one-time code, card number or any payment detail.
- Never create an account, register a card, press Submit or pay for the person.
- Never put a file number, name or any case detail in a URL.
- Only send people to the addresses in [cso_links.json](cso_links.json). Tell them to open the page in their own browser.
- If the person pastes a screenshot, ask them to crop out names, card details and file numbers first.

## The questions to ask, in order

Ask one at a time and wait for the answer.

1. **"Do you have a CSO account that can e-file?"**
   - *Yes* → go to question 2.
   - *No* or *not sure* → explain the two steps under **Accounts** (an identity such as a Basic BCeID, then registering it with CSO) and send them to the **register** page once they have the identity. A person who has used other B.C. government online services may already have one, so ask them to check first.
2. **"Are you logged on to CSO in your browser right now?"**
   - *No* → send them to the **logon** page (alternatives: BC Services Card or BCeID through BC Registry Service).
   - *Yes* → send them to **E-file home** and tell them to choose **Application Records** in the left-hand E-file menu, **not** Submit Package.
3. **"Is a credit card registered on your CSO account?"**
   - *No* or *not sure* → explain that CSO blocks filing until a card is registered, and walk them through **Credit card requirement** below. They enter card details only on CSO's own payment page.
   - *Yes* → continue.
4. **"Is your binder ready?"** Run the 20-gate validation, then give the file-size route and the filing checklist below.

## Accounts: two steps

Registering is **two steps**: first get an identity that CSO accepts, then register that identity with CSO. Anyone who has used other B.C. government online services may already have the first part.

**Step A: an identity CSO accepts** (any one of these)

| Identity | Notes |
| :--- | :--- |
| **Basic BCeID** | For one individual. Can register a credit card. Cannot add other users. Apply at bceid.ca/register or call the BCeID Help Desk, 1-888-356-2741 (8:30 a.m. to 4:30 p.m., Monday to Friday). |
| **Business BCeID** | For a business or when several people will share one CSO account. Can register a card and add users. Same application route. |
| **BC Services Card** | For eligible B.C. residents. |
| **Premium BC Registries and Online Services account** | Adds draw-down or pre-authorized-debit payment. Created through the BC Registries website. |
| IDIR | Internal B.C. Government staff only. Email CSO Support (Courts.CSO@gov.bc.ca) with the IDIR details and the Account Manager's name. |

The guide suggests a **Basic BCeID** for a person who is the only CSO user.

**Step B: register with CSO** (from the CSO registration guide)

1. On the CSO home page click **Register**, read the registration information, click **Continue**.
2. Sign in with the BCeID or BC Services Card.
3. Read and accept the CSO Electronic Search Service Agreement. Registration cannot continue without accepting.
4. Confirm the account profile: Business Name, Business Type, Business Email (entered twice).
5. Enter the Account Manager: name and email (entered twice). The Account Manager manages the account and users.
6. Print or save the **activation confirmation** (service type, activation date and time, CSO account name and number, Account Manager, CSO Client ID). It is needed when contacting CSO Support.

**Always sign in to CSO with the BCeID or BC Services Card, never the CSO Client ID.** Keep a back-up Account Manager if there are several users.

For searching court files no account is needed. A credit card or premium BC Registries account pays the fees.

## Credit card requirement

Before any submission the account must have an **active registered credit card**. Without one, e-filing stops with **"No Registered Credit Card — You must have an active registered credit card before you can submit a filing package."** (seen in a logged-on screenshot).

Tell people to register the card **well before the filing deadline**, not on filing day. From the CSO registration guide, once the CSO account is activated:

- **Where:** log on, then in the left-hand menu choose **Profile → Register Credit Card**. This is confirmed by a logged-on screenshot of the page (`/cso/clients/creditCardRegOptions.do`); the Profile menu there lists My Profile, Register Credit Card, Monthly Statement, Refund Requests and View Refund Requests. The page has a **Register Credit Card** button. The CSO eFile help text gives the same path, and the registration guide adds an **Account** option for a card shared by the whole account.
- **Corporate cards:** the page warns that a corporate credit card must have been registered for government services with the card's financial institution before it will work.
- **Account** card: everyone on the account can charge to it, but each user must be authorized (Account → Manage Users → View Details → "Authorize user to charge services to registered credit card").
- **My Profile** card: charges only that user. A user without their own card defaults to the Account Manager's card.
- The page says registering a card is optional in general; **e-filing requires it**. Clicking Register Credit Card sends the person to the Provincial Treasury's Internet Payments program. The card details are stored there, not by CSO. The person enters card type, number, expiry date and security code on that page and clicks Submit. A confirmation screen appears; the guide recommends printing it.
- If the menu differs from what is described here, tell the person to look under Profile (or Account) and to contact support.
- **Why a card must be on file:** registry staff review a submission before payment is taken, which can be minutes to days later (a document submitted after 4:00 p.m. on a Friday is reviewed the following Monday). The card on file lets the registry take payment when it accepts the filing. Once registered, the card does not have to be re-entered for each submission.
- Payment goes through the Provincial Treasury's Internet Payments System (BC ExpressPay). Accepted cards: Visa, Visa Debit, MasterCard, MasterCard Debit and American Express. A premium BC Registries and Online Services account can pay instead.

## Support contacts

- **CSO Support Centre:** 1-800-663-6102 (toll-free), 8:30 a.m. to 4:30 p.m. Pacific, Monday to Friday except statutory holidays (CSO eFile help text and FAQ). Email for court-registry or filing questions: Courts.CSO@gov.bc.ca. The CSO FAQ lists the same number, with BCOLHELP@gov.bc.ca, for eSearch, payments, refunds and account setup.
- **BC OnLine and BC Registry and Online Services users:** 1-877-370-1033 (CSO registration guide).
- **BCeID Help Desk:** 1-888-356-2741, 8:30 a.m. to 4:30 p.m., Monday to Friday.

## Which filing service to use

After log on, the left-hand **E-file** menu shows: Submit Package, View Packages, Upload Large Files, Current Processing Times, **Application Records**.

- **Application Records** is the service for a binder. The April 2026 guide calls it "Submit Application Records"; the live menu label is **Application Records**.
- **Submit Package** is a different flow (six steps: Identification, Access, Documents, Parties, Request Access, Review Package). It is not for application records.
- **Upload Large Files** is a prerequisite for files over 20 MB.

## Scope of e-filing

- **PDF only.** It is the filer's responsibility that the PDF is readable and complete. A document that cannot be made into a PDF must be taken to the registry.
- E-filing covers most civil matters in B.C. Supreme Court, Small Claims in Provincial Court and civil matters in the Court of Appeal. It is **not** available for Supreme Court probate or criminal matters. Provincial Court family e-filing was described as "expected soon".
- Registration requires accepting an Electronic Services Agreement with Court Services Branch; the agreement appears during account creation.
- A **filing package** is one or more documents for the same case file, filed together.

## What the person sees after log on (from screenshots, 2026-11-01)

- **E-File Home Page** (`/cso/filing/submission/efileHome.do`): "From here you can file packages and view existing packages." A **Go to** box lists Add Package, Add Court Of Appeal Package, View Packages, Upload Large Files and Current Processing Times, and a **Your Filed Packages** list ("No packages could be found" before the first filing). The left menu also lists Submit Package, View Packages, Upload Large Files, Current Processing Times and **Application Records**.
- **Add Package / Submit Package** is for filing documents into a court file, not for a binder. Its **Step 1: Identification** asks: new court file or existing file; filing information (location to file with its 3-letter registry code, level of court, class of case); whether the document was previously rejected; whether a fee waiver order applies; whether it is a CFCSA file; whether it contains a protection or restraining order (automatic rush processing); whether to request urgent (rush) processing; whether to send email notification (a default CSO email is used, with an optional second email entered twice); and the person's own file number. The later steps are Access, Documents, Parties, Request Access (restricted files) and Review Package.
- Once a card is registered, the "No Registered Credit Card" block no longer appears and the Step 1 form opens.
- The Step 1 fields (location, level, class, file number) are the same details the April 2026 guide lists for Application Records, so the person should have them ready before starting either flow.
- Never copy a person's email address, name or file number from screenshots into documentation or examples.

## Filing checklist for an application record

From the April 2026 guide (repository copy) and the CSO FAQ:

- **Size route:** up to 20 MB, upload directly. Over 20 MB and up to 50 MB, first use **Upload Large Files** (the upload stays available for submission for 3 hours), then select it from the *Select Large File* list. Over 50 MB cannot be submitted; optimise the PDF.
- **Fees:** a $7.00 CSO transaction fee, on top of any statutory filing fees, charged to the registered card. The CSO eFile help text says the $7.00 is charged per filing package **whether or not it is accepted**, and **again** when documents are re-submitted after a courtesy correction or rejection (stated for eFile packages; *not confirmed* for application records). Users with indigent status are not charged the $7.00. Statutory fees are collected when registry staff process the document.
- **Fields CSO asks for:** file number, location (3-letter registry code), level (S for Supreme), class (for example S Supreme civil general, H foreclosure, E family law proceeding), appearance date.
- **Document type:** Application Record, Petition Record, Hearing Record, Book of Authorities or Individual Document. Submit the binder as **one PDF**, not separate documents.
- **Sequence number:** type one for each upload. The application record is **1**; a book of authorities is **2**. Reusing a number **overwrites** the earlier upload. A corrected record must reuse the **same** number to replace the original.
- **Deadline:** 4:00 p.m. on the business day that is one full business day before the hearing. Late records are not placed on the hearing list. Corrections have the same deadline. Records are checked, and non-compliant ones are rejected by email.
- **Deemed filing time:** under Supreme Court Rule 23-3(14), an accepted e-filed document received at or before 4:00 p.m. on a day the registry is open is deemed filed that day; otherwise the next business day the registry is open. Orders are the exception: they are dated the day the order is signed. CSO itself is available 24 hours a day, but the registry works to its own hours.
- **Order to be signed on the bench:** submit the vetted order through **eFiling**, not the Application Record service, and indicate the hearing date.
- **After submitting:** a confirmation message appears and an email is sent. Keep the email. If the matter is adjourned to a specific date the record stays; if adjourned generally, resubmit when the matter is reset.
- **Eligibility:** matters of 30 minutes or less before an Associate Judge. Virtual chambers list applies to all locations except Vancouver; New Westminster from June 1, 2026. Foreclosure sale approvals cannot go on the virtual list.

## Browser notes

CSO supports Microsoft Edge or Google Chrome, and Safari on Mac. Daily filing cut-offs follow registry hours even though CSO is available 24 hours a day.

## Not verified yet

- The address and fields of the **Application Records** screen itself (screenshots so far show Submit Package, not Application Records). Ask the person to read you any message they see (without card or case details) rather than guessing.
- Whether a corrected **application record** is charged the $7.00 again (the eFile help says so for eFile packages).
- The content of the CSO notice linked from the home page (31 March 2026 news item).
