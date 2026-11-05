Feature: Operator Authentication and Clearance Enforcement
  As a Substation Operations Engineer
  I want operator clearance to be strictly enforced before supervisory controls are unlocked
  So that unauthenticated or unauthorized users cannot trip medium-voltage circuit breakers

  @bdd @security @auth
  Scenario: Valid operator authentication grants supervisory control clearance
    Given the SCADA API is available and healthy
    When the operator "operator_alice" submits valid credentials "ControlRoom2026!"
    Then the authentication response must return HTTP status 200
    And the user profile must confirm role "OPERATOR"
    And an access token must be issued

  @bdd @security @auth
  Scenario: Unauthorized viewer cannot dispatch power setpoints
    Given an authenticated session for user "viewer_guest" with role "VIEWER"
    When the viewer attempts to dispatch a power setpoint of 5.0 MW
    Then the system must reject the command with HTTP status 403

