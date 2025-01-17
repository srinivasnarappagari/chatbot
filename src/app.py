import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from pandasai import PandasAI
from pandasai.llm.openai import OpenAI
import plotly.graph_objects as go
import plotly.express as px
from pandas.api.types import is_numeric_dtype


load_dotenv()

class CSVDataExplorer:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.df = None
        self.result = None
        self.llm = OpenAI(api_token=self.openai_api_key)
        self.pandas_ai = PandasAI(self.llm)

    def load_data(self, file):
        if file is not None:
            self.df = pd.read_csv(file)

    def chat_with_csv(self, prompt):
        if self.df is None:
            return "Please upload a CSV file first."
        try:
            self.result = self.pandas_ai.run(self.df, prompt=prompt)  # Assign value to the class variable
            self.extract_columns(self.result)  # Extract columns from the response
            return self.result
        except Exception as e:
            return f"An error occurred: {e}"

    def describe_dataframe(self, df):
        if df is None:
            return "DataFrame is empty or not loaded."
        return df.describe()

    def show_dataframe_columns(self, df):
        if df is None:
            return "DataFrame is empty or not loaded."
        return df.columns

    def save_dataframe_to_csv(self, df, filename):
        if df is None:
            return "DataFrame is empty or not loaded."
        df.to_csv(filename, index=False)
        return f"DataFrame saved to {filename} successfully."

    def extract_columns(self, result):
        if "output" in result:
            output_text = result["output"]["output_text"]
            columns = [col.strip() for col in output_text.split(",") if is_numeric_dtype(self.df[col.strip()])]
            return columns
        return []
       

def main():
    result = None
    st.set_page_config(layout='wide')
    st.title("Chat Bot 👨‍💻👨‍💻")

    csv_data_explorer = CSVDataExplorer()

    input_csv = st.file_uploader("Upload your CSV file", type=['csv'])

    if st.button("Clear Data"):
        csv_data_explorer.df = None

    if input_csv is not None:
        csv_data_explorer.load_data(input_csv)
        st.info("CSV Uploaded Successfully")

    if csv_data_explorer.df is not None:
        col1, col2,col3,col4 = st.columns([1, 1, 1, 1])

        with col1:
            st.info("Data Preview")
            st.dataframe(csv_data_explorer.df, use_container_width=True)

        with col2:
            st.info("Chat Below")
            input_text = st.text_area("Enter your query", key="input_query")

            if input_text is not None and st.button("Chat with CSV"):
                st.info("Your Query: " + input_text)
                result = csv_data_explorer.chat_with_csv(input_text)

                if "describe" in input_text.lower():
                    st.success("DataFrame Description:")
                    description = csv_data_explorer.describe_dataframe(csv_data_explorer.df)
                    st.table(description)

                elif "show columns" in input_text.lower():
                    st.success("DataFrame Columns:")
                    columns = csv_data_explorer.show_dataframe_columns(csv_data_explorer.df)
                    st.write(columns)

                elif "save output df into a csv file" in input_text.lower():
                    filename = "output.csv"
                    result = csv_data_explorer.save_dataframe_to_csv(csv_data_explorer.df, filename)
                    st.success(result)
                elif "show int" in input_text.lower():
                    int_columns = [col for col in csv_data_explorer.df.columns if pd.api.types.is_integer_dtype(csv_data_explorer.df[col])]
                    st.success("Integer Columns:")
                    st.write(int_columns)
                    # Display data from integer columns
                    st.dataframe(csv_data_explorer.df[int_columns])

                else:
                    st.write(result)
        with col4:
                try:
                    if isinstance(result, pd.DataFrame):
                        if result is not None:
                            st.info("Data Visualizations")
                            for col in result.columns:
                                if result[col].dtype == 'object':
                                    fig = px.bar(result, x=col, title=f"Bar Plot for {col}")
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    fig = px.histogram(result, x=col, title=f"Histogram for {col}")
                                    st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error("Not a pandas DataFrame")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        with col3:
            try:
                if isinstance(result, pd.DataFrame):
                    if result is not None:
                        st.info("Bar Plot & Line Plot")
                        if result is not None:
                            # Convert the DataFrame to long-form
                                result_df_long = pd.melt(result.reset_index(), id_vars='index', var_name='Column', value_name='Value')

                                # Create bar plots for each column
                                fig = go.Figure()
                                for col in result_df_long['Column'].unique():
                                    fig.add_trace(go.Bar(x=result_df_long[result_df_long['Column'] == col]['index'],
                                                            y=result_df_long[result_df_long['Column'] == col]['Value'],
                                                            name=col))
                                fig.update_layout(barmode='group', xaxis_title='Index', yaxis_title='Value', title="Bar Plot for Columns")
                                st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Not a pandas DataFrame")               
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")


            if result is not None and isinstance(result, pd.DataFrame):
                # Check the number of numeric columns in the DataFrame
                numeric_columns = result.select_dtypes(include='number').columns
                if len(numeric_columns) >= 1:
                    # If there is one or more numeric columns, create a line plot
                    fig = px.line(result, x=result.index, y=numeric_columns,
                                title="Line Plot")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("The output DataFrame does not have any numeric columns for a line plot in Col3.")
            else:
                st.warning("No output DataFrame available for the line plot")

if __name__ == "__main__":
    main()
