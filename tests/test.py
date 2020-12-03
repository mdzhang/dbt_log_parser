SAMPLE_LOG = """
Running with dbt=0.15.2
Found 469 models, 1658 tests, 0 snapshots, 0 analyses, 300 macros, 0 operations, 0 seed files, 204 sources
19:02:13 | Concurrency: 30 threads (target='prod')

19:02:13 | 2 of 1100 START test accepted_values_dim_cur_gift_card_delivery_mode__Print_at_Home__Send_by_Email [RUN]
19:02:15 | 1 of 1100 PASS accepted_values_dim_cur_bronto_contact_bronto_status__active__onboarding__transactional__bounce__unconfirmed__unsub [\x1b[32mPASS\x1b[0m in 2.11s]
19:02:15 | 12 of 1100 PASS is_gte_zero_fact_item_promo_slot_purchases_cost...... [\x1b[32mPASS\x1b[0m in 2.08s]
19:02:27 | 271 of 1100 FAIL 548326 unique_int_home_page_display_resources_you_may_like_event_user_id [\x1b[31mFAIL 548326\x1b[0m in 1.16s]
19:03:42 | Finished running 1100 tests in 97.47s.
\x1b[31mCompleted with 14 errors and 3 warnings:\x1b[0m

\x1b[31mFailure in test unique_int_home_page_display_resources_you_may_like_event_user_id (models/intermediate/int_home_page_display_resources_you_may_like.yml)\x1b[0m
  Got 548326 results, expected 0.

  compiled SQL at target/compiled/core/schema_test/unique_int_home_page_display_resources_you_may_like_event_user_id.sql

\x1b[33mWarning in test is_gte_zero_dim_school_access_subscriptions_subscription_term_length (models/dimensional/dim_school_access_subscriptions.yml)\x1b[0m
  Got 5 results, expected 0.

  compiled SQL at target/compiled/core/schema_test/is_gte_zero_dim_school_access_subscriptions_subscription_term_length.sql
"""