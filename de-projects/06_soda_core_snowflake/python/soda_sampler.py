from soda.scan import Scan
from soda.sampler.sampler import Sampler
from soda.sampler.sample_context import SampleContext


# Create a custom sampler by extending the Sampler class
class CustomSampler(Sampler):
    def store_sample(self, sample_context: SampleContext):
        # Retrieve the rows from the sample for a check
        rows = sample_context.sample.get_rows()
        # Check SampleContext for more details that you can extract
        # This example simply prints the failed row samples
        print(sample_context.query)
        print(sample_context.sample.get_schema())
        print(rows)


if __name__ == '__main__':
    # Create Scan object
    s = Scan()
    # Configure an instance of custom sampler
    s.sampler = CustomSampler()

    s.set_scan_definition_name("test_scan")
    s.set_data_source_name("snowflake")
    s.add_configuration_yaml_file(file_path="./soda/configuration.yml")
    s.add_sodacl_yaml_file("./soda/checks/orders.yml")

    s.execute()
    print(s.get_logs_text())