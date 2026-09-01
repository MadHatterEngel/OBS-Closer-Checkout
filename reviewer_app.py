    def fetch_logs():
        try:
            # Removed 'photo_data' since that column was deprecated and doesn't exist
            response = supabase.table('closing_logs').select('id, timestamp, employee_name, station, image_url, status').order('id', desc=True).limit(250).execute()
            return response.data
        except Exception as e:
            st.error(f"Database error: {str(e)}")
            return []
