# Attraction Recommendation and Reservation - BSRL Specification

Owner: Member C  
Service provider: Municipal Culture & Recreation Services  
Service: Attraction Recommendation and Reservation Service

## Service Identification

The service helps a citizen find a suitable city attraction and reserve a visit
when capacity is available. It is a selected microservice in ServiceUniverse and
is exposed through the shared API Gateway.

## Business Service

```text
Business service AttractionRecommendationAndReservation
provided by MunicipalCultureAndRecreationServices
consumed by Citizen
```

The service realizes two business capabilities:

- `RecommendAttractions`: rank available attractions by preference, date, rating,
  opening day, and remaining daily capacity.
- `ReserveAttractionVisit`: create and manage a reservation for a selected
  attraction.

## Actors And Roles

| Actor | Role | Responsibility |
|---|---|---|
| Citizen | Service consumer | Enters visit preferences, selects an attraction, and confirms reservation details. |
| Municipal Culture & Recreation Services | Service provider | Publishes attractions, capacity rules, opening days, and reservation policies. |
| Attraction Reservation Microservice | Service participant | Validates availability, creates reservations, and enforces status transitions. |
| API Gateway | Service mediator | Provides the public endpoint and converts downstream errors into the platform envelope. |

## Service Contract

### Recommend Attractions

Input:

- `visit_date`
- `visitor_count`
- optional `district`
- optional `category`
- optional `indoor`
- optional `min_rating`

Output:

- ranked attraction list
- `available_capacity`
- `recommendation_score`

Rules:

- Attractions closed on the requested date are excluded.
- Attractions with remaining capacity below `visitor_count` are excluded.
- When `recommend=true`, results are ordered by recommendation score.

### Create Reservation

Input:

- `attraction_id`
- `citizen_id`
- `visit_date`
- `visitor_count`
- optional `contact_phone`

Output:

- `reservation_id`
- selected attraction
- visit date
- visitor count
- reservation status

Rules:

- The attraction must exist.
- The attraction must be open on the requested date.
- Remaining daily capacity must be sufficient.
- One reservation can include 1 to 10 visitors.
- Created reservations enter `confirmed` status.

## States

Allowed reservation states:

- `pending`
- `confirmed`
- `completed`
- `cancelled`

Allowed transitions:

```text
pending -> confirmed
pending -> cancelled
confirmed -> completed
confirmed -> cancelled
completed -> terminal
cancelled -> terminal
```

## Business Errors

| Code | Meaning |
|---|---|
| `ATTRACTION_NOT_FOUND` | The requested attraction does not exist. |
| `ATTRACTION_CLOSED` | The attraction is closed on the requested date. |
| `CAPACITY_CONFLICT` | Remaining capacity is lower than requested visitor count. |
| `RESERVATION_NOT_FOUND` | The reservation cannot be found. |
| `INVALID_RESERVATION_STATUS` | The requested status transition is not allowed. |

## Traceability To Implementation

- Service implementation: `services/attraction_reservation/app/main.py`
- Gateway route: `gateway/app/routers/attraction_reservation.py`
- Frontend page: `frontend/templates/services/attraction-reservation.html`
- Contract: `contracts/schemas/attraction-reservation.openapi.yaml`
