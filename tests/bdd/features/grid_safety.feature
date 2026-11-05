Feature: Medium-Voltage UPS Grid Firewall Isolation and Data Center Protection
  As a Critical Facilities Operations Director
  I want the MV-UPS to isolate the facility into islanded mode during severe utility grid faults
  So that sensitive data center server racks receive uninterruptible, clean power

  @bdd @resilience @grid_safety
  Scenario: Automatic firewall islanding upon utility grid voltage collapse
    Given the MV-UPS is operating normally in "GRID_CONNECTED" mode
    And the data center load is stable
    When a severe grid under-voltage disturbance is simulated
    Then the MV-UPS firewall status must transition to "ISLANDED"
    And the circuit breaker CB-101 status must change to "TRIPPED"
    And a critical alarm "GRID_UNDER_VOLTAGE" must be annunciated
