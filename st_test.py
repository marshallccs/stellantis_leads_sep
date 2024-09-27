# gb.configure_column(
#     field='yourField',  # Your original field
#     header_name='Your Header',
#     pivot=True
# )

# # Assuming you want to reference pivoted columns in a valueGetter
# gb.configure_column(
#     field='calculatedField',
#     header_name='Calculated Field',
    # valueGetter="""
    #     function(params) {
    #         const pivotValue = params.data[params.colDef.field]; // Access the pivoted column value
    #         const anotherValue = params.data['someOtherField']; // Access another field if needed

    #         // Perform your calculation or expression here
    #         return pivotValue + anotherValue; // Example expression
    #     }
    # """
# )
