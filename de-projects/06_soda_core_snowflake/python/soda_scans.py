from soda.scan import Scan

scan = Scan()
scan.set_data_source_name("snowflake")

# Add configuration YAML files
scan.add_configuration_yaml_file(file_path="./soda/configuration.yml")

# Add variables
scan.add_variables({"date": "2024-01-24"})

# Add check YAML files 
scan.add_sodacl_yaml_file("./soda/checks/orders.yml")
scan.add_sodacl_yaml_file("./soda/checks/returned_orders.yml")

# Execute the scan
#scan.execute()
exit_code = scan.execute()
print(exit_code)

# Set logs to verbose mode, equivalent to CLI -V option
scan.set_verbose(True)

# Print results of scan
#print("Here is the result of your scan")
print(scan.get_logs_text())

# Set scan definition name, equivalent to CLI -s option;
#scan.set_scan_definition_name("YOUR_SCHEDULE_NAME")

# Inspect the scan result
#print(scan.get_scan_results()) #returns result as json

# Inspect the scan logs
#scan.get_logs_text() # returns result as text log as you see in CLI

# Typical log inspection # Important feature - used to build automated pipelines
#print(scan.assert_no_error_logs())
#print(scan.assert_no_checks_fail())

# Advanced methods to inspect scan execution logs
#print(scan.has_error_logs())
#print(scan.get_error_logs_text())

# Advanced methods to review check results details
#print(scan.get_checks_fail())
#print(scan.has_check_fails())
#print(scan.get_checks_fail_text())
#print(scan.assert_no_checks_warn_or_fail())
#print(scan.get_checks_warn_or_fail())
#scan.has_checks_warn_or_fail()
#scan.get_checks_warn_or_fail_text()
#print(scan.get_all_checks_text())