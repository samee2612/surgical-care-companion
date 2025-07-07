# TKA Voice Agent Call Scheduling Tests

This directory contains comprehensive test cases for the TKA Voice Agent call scheduling logic.

## Overview

The call scheduling system automatically generates 6 scheduled calls for each patient based on their surgery date:

| Days from Surgery | Call Type    | Purpose                               |
|-------------------|--------------|---------------------------------------|
| -42               | enrollment   | Initial patient enrollment and setup  |
| -28               | education    | Pre-operative education session       |
| -21               | education    | Additional education and preparation  |
| -14               | preparation  | Pre-operative preparation check       |
| -7                | preparation  | Final preparation and readiness       |
| -1                | final_prep   | Day-before surgery final check        |

## Test Coverage

### `test_call_scheduling.py`

The main test file contains 11 comprehensive test cases:

1. **`test_correct_number_of_calls_scheduled`** - Verifies exactly 6 calls are created
2. **`test_call_schedule_dates_calculation`** - Tests date calculations relative to surgery date
3. **`test_call_types_assignment`** - Validates correct call types are assigned
4. **`test_all_calls_marked_as_scheduled`** - Ensures all calls start with 'scheduled' status
5. **`test_surgery_type_propagation`** - Tests surgery type is correctly set in all calls
6. **`test_different_surgery_dates`** - Tests scheduling across different months/years
7. **`test_weekend_scheduling`** - Verifies calls are scheduled even on weekends
8. **`test_call_patient_id_association`** - Tests proper patient-call relationships
9. **`test_get_patient_calls_endpoint`** - Tests the API endpoint for retrieving calls
10. **`test_edge_case_leap_year`** - Tests scheduling during leap year scenarios
11. **`test_full_patient_enrollment_flow`** - Complete integration test

## Running Tests

### Prerequisites

1. **PostgreSQL Running**: Ensure the PostgreSQL container is running
   ```bash
   docker-compose up -d postgres
   ```

2. **Test Dependencies**: Install test dependencies
   ```bash
   pip install -r requirements-test.txt
   ```

### Running Tests

**Option 1: Using the test runner script**
```bash
cd backend
python run_tests.py
```

**Option 2: Using pytest directly**
```bash
cd backend
python -m pytest tests/test_call_scheduling.py -v
```

**Option 3: Running a specific test**
```bash
cd backend
python -m pytest tests/test_call_scheduling.py::TestCallScheduling::test_correct_number_of_calls_scheduled -v
```

## Test Database

The tests use a PostgreSQL test database (`tka_voice_test`) to support all PostgreSQL-specific features like ARRAY types used in the CallSession model.

- **Test Database**: `tka_voice_test`
- **Connection**: Uses same credentials as main database
- **Isolation**: Each test gets a fresh database session with cleanup

## Key Features Tested

### Date Calculations
- Correct calculation of dates relative to surgery date
- Handling of different surgery dates (January, June, December)
- Leap year support
- Weekend scheduling

### Call Scheduling Logic
- Proper assignment of call types based on timeline
- Correct `days_from_surgery` values
- All calls marked as 'scheduled' initially
- Surgery type propagation to all calls

### API Integration
- Patient enrollment with automatic call generation
- Call retrieval endpoints
- Error handling and validation

### Database Operations
- Proper patient-call relationships
- Transaction handling
- Data integrity

## Test Results

All 11 tests currently pass, validating:
- ✅ Correct number of calls (6) are scheduled
- ✅ Date calculations work correctly
- ✅ Call types are properly assigned
- ✅ API endpoints function correctly
- ✅ Database relationships are maintained
- ✅ Edge cases are handled (leap year, weekends)

## Extending Tests

To add new test cases:

1. Add new test methods to the `TestCallScheduling` class
2. Use the `db_session` fixture for database access
3. Use the `sample_patient_data` fixture for consistent test data
4. Follow the existing naming convention: `test_description_of_what_is_tested`

The test framework is designed to be easily extensible for additional call scheduling features. 