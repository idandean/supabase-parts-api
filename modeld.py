import pandas as pd
from tabulate import tabulate
import os
from supabase import create_client, Client

# Supabase configuration from environment variables
import os
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Helper function to convert columns to string type
def ensure_string_columns(df, columns):
    """Convert specified columns to string type to prevent str accessor errors"""
    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype(str)
    return df

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_data_from_supabase():
    """Load all necessary data from Supabase tables."""
    try:
        print(f"Connecting to Supabase... URL configured: {'Yes' if SUPABASE_URL else 'No'}")
        print(f"API Key configured: {'Yes' if SUPABASE_KEY else 'No'}")
        
        # Fetch data from Supabase tables using correct table names
        prodinfo_response = supabase.table("prodinfo").select("*").execute()
        pnc_name_response = supabase.table("pnc_name").select("*").execute()
        pninfo_response = supabase.table("pninfo").select("*").execute()
        pninfo2_response = supabase.table("pninfo2").select("*").execute()
        model_d_response = supabase.table("modeld").select("*").execute()

        # Convert to dataframes
        prodinfo_df = pd.DataFrame(prodinfo_response.data)
        pnc_name_df = pd.DataFrame(pnc_name_response.data)
        pninfo_df = pd.DataFrame(pninfo_response.data)
        pninfo2_df = pd.DataFrame(pninfo2_response.data)
        model_d_df = pd.DataFrame(model_d_response.data)

        # Print data for debugging
        print("Data samples received:")
        print(f"prodinfo rows: {len(prodinfo_df) if not prodinfo_df.empty else 0}")
        print(f"pnc_name rows: {len(pnc_name_df) if not pnc_name_df.empty else 0}")
        
        # Clean column names without using .str accessor
        for df in [prodinfo_df, pnc_name_df, pninfo_df, pninfo2_df, model_d_df]:
            # Convert column names manually
            df.columns = [str(col).strip().upper() for col in df.columns]

        print("✅ All data loaded successfully from Supabase.")
        return prodinfo_df, pnc_name_df, pninfo_df, pninfo2_df, model_d_df

    except Exception as e:
        print(f"❌ Error loading data from Supabase: {e}")
        import traceback
        print(traceback.format_exc())
        exit()

# Load all data at startup
try:
    prodinfo_df, pnc_name_df, pninfo_df, pninfo2_df, model_d_df = load_data_from_supabase()
except Exception as e:
    print(f"Failed to load initial data: {e}")
    import traceback
    print(traceback.format_exc())
    exit()

def get_s_code_and_p_date():
    m_code = input("\nEnter M_CODE (Model Code): ").strip().upper()
    frame_no = input("Enter FRAME_NO (Serial Number): ").strip()

    # Convert columns to string type to prevent .str accessor errors
    ensure_string_columns(prodinfo_df, ["M_CODE", "FRAME_NO"])
    
    # Check for exact match (M_CODE + FRAME_NO)
    match = prodinfo_df[(prodinfo_df["M_CODE"].str.upper() == m_code) & 
                        (prodinfo_df["FRAME_NO"].str.upper() == frame_no)]

    if not match.empty:
        s_code = match.iloc[0]["S_CODE"]
        p_date = match.iloc[0]["P_DATE"]
        print("\n✅ Forklift Details Found:")
        # Filter out unnecessary columns if they exist
        display_cols = [col for col in match.columns if col not in ["SOP_CODE", "OP_CODE", "OP_CODE2", "SOP_CNT", "OP_CNT"]]
        print(match[display_cols])
        return s_code, p_date

    print("⚠ No exact match for FRAME_NO. Checking for S_CODE by M_CODE...")
    matches = prodinfo_df[prodinfo_df["M_CODE"].str.upper() == m_code]

    if not matches.empty:
        print("\n🔹 Multiple P_DATE options found. Choose one:")
        for i, row in matches.iterrows():
            print(f"{i+1}. S_CODE: {row['S_CODE']}, P_DATE: {row['P_DATE']}")

        choice = int(input("Enter your choice (number): ")) - 1
        s_code = matches.iloc[choice]["S_CODE"]
        p_date = matches.iloc[choice]["P_DATE"]
        return s_code, p_date

    print("❌ No records found.")
    return None, None

def get_pnc():
    # Dictionary of part synonyms - mapping common terms to official part names
    part_synonyms = {
        "RADIATOR ASSY": ["COOLING SYSTEM", "COOLANT SYSTEM", "COOLER", "HEAT EXCHANGER", "RADIATOR"],
        "HYDRAULIC CYLINDER": ["LIFT CYLINDER", "HYDRAULIC RAM", "TILT CYLINDER", "CYLINDER"],
        "BATTERY": ["POWER SUPPLY", "BATTERY PACK", "POWER CELL", "ELECTRIC BATTERY"],
        "BRAKE ASSY": ["BRAKING SYSTEM", "BRAKE KIT", "BRAKES", "BRAKE ASSEMBLY"],
        "STEERING WHEEL": ["WHEEL", "DRIVER WHEEL", "STEERING", "CONTROL WHEEL"],
        "FORK": ["TINES", "LIFTING FORK", "FORK ARM", "PALLET FORK"],
        "ENGINE": ["MOTOR", "POWER UNIT", "DRIVE UNIT", "POWER PLANT"],
        "TRANSMISSION": ["GEARBOX", "TRANSAXLE", "DRIVE TRAIN", "GEAR SYSTEM"],
        "MAST": ["LIFTING MAST", "TOWER", "UPRIGHT", "LIFTING TOWER"],
        "SEAT": ["DRIVER SEAT", "OPERATOR SEAT", "CHAIR", "SITTING UNIT"],
        "TIRE": ["WHEEL", "RUBBER", "WHEEL TIRE", "TYRE"],
        "HYDRAULIC PUMP": ["FLUID PUMP", "HYDRAULIC MOTOR", "PRESSURE PUMP", "OIL PUMP"],
        "FILTER": ["AIR FILTER", "OIL FILTER", "FUEL FILTER", "FILTRATION UNIT"],
        "BEARING": ["WHEEL BEARING", "ROLLER BEARING", "BALL BEARING", "SHAFT BEARING"],
        "CONTROL VALVE": ["HYDRAULIC VALVE", "VALVE BODY", "PRESSURE VALVE", "FLOW CONTROL"],
        "ALTERNATOR": ["GENERATOR", "POWER GENERATOR", "CHARGING UNIT", "ELECTRIC GENERATOR"],
        "STARTER": ["STARTER MOTOR", "IGNITION STARTER", "ELECTRIC STARTER", "STARTING UNIT"],
        "HEADLIGHT": ["LIGHT", "LAMP", "FRONT LIGHT", "ILLUMINATION"],
        "HORN": ["ALARM", "WARNING HORN", "SIGNAL HORN", "BEEPER"],
        "FUEL PUMP": ["GAS PUMP", "PETROL PUMP", "DIESEL PUMP", "FUEL DELIVERY"],
    }
    
    part_name = input("\nEnter the type of part you need (e.g., Radiator Assy, Cooling System): ").strip().upper()
    
    # Ensure DESC_ENG column is string type
    ensure_string_columns(pnc_name_df, ["DESC_ENG"])
    
    # First check for exact match
    match = pnc_name_df[pnc_name_df["DESC_ENG"].str.upper() == part_name]
    
    if not match.empty:
        pnc = match.iloc[0]["PNC"]
        print(f"✅ Found exact match PNC: {pnc}")
        return pnc
    
    # If no exact match, check if input matches any synonym
    matched_official_name = None
    
    # Check if input contains or matches any synonym
    for official_name, synonyms in part_synonyms.items():
        if any(synonym in part_name for synonym in synonyms) or any(part_name in synonym for synonym in synonyms):
            matched_official_name = official_name
            print(f"🔍 Recognized '{part_name}' as '{official_name}'")
            break
    
    # If found a match through synonyms
    if matched_official_name:
        match = pnc_name_df[pnc_name_df["DESC_ENG"].str.upper() == matched_official_name]
        if not match.empty:
            pnc = match.iloc[0]["PNC"]
            print(f"✅ Found PNC: {pnc} for {matched_official_name}")
            return pnc
    
    # If still no match, try partial string matching
    print("\n⚠ Trying partial name matching...")
    potential_matches = pnc_name_df[pnc_name_df["DESC_ENG"].str.upper().str.contains(part_name)]
    
    if potential_matches.empty:
        # If no partial match either, try looking for individual words
        input_words = part_name.split()
        for word in input_words:
            if len(word) >= 3:  # Only check words of reasonable length
                word_matches = pnc_name_df[pnc_name_df["DESC_ENG"].str.upper().str.contains(word)]
                if not word_matches.empty:
                    potential_matches = pd.concat([potential_matches, word_matches]).drop_duplicates()
    
    if not potential_matches.empty:
        print("\n🔍 Found potential matches:")
        for i, row in potential_matches.iterrows():
            print(f"{i+1}. {row['DESC_ENG']}")
        
        choice = input("\nSelect the correct part (number) or 0 to cancel: ").strip()
        if choice.isdigit() and int(choice) > 0 and int(choice) <= len(potential_matches):
            selected_idx = int(choice) - 1
            pnc = potential_matches.iloc[selected_idx]["PNC"]
            print(f"✅ Selected PNC: {pnc}")
            return pnc
    
    print("❌ No matching PNC found.")
    return None

def get_part_no(s_code, p_date, pnc):
    # Convert columns to string type before using str methods
    ensure_string_columns(pninfo_df, ["S_CODE", "PNC"])
    ensure_string_columns(pninfo2_df, ["S_CODE", "PNC"])
    
    matches_pninfo = pninfo_df[
        (pninfo_df["S_CODE"].str.upper() == s_code) &
        (pninfo_df["PNC"].str.upper() == pnc) &
        ((pninfo_df["P_START"].isna()) | (pninfo_df["P_START"] <= p_date)) & 
        ((pninfo_df["P_END"].isna()) | (pninfo_df["P_END"] >= p_date))
    ]

    matches_pninfo2 = pninfo2_df[
        (pninfo2_df["S_CODE"].str.upper() == s_code) &
        (pninfo2_df["PNC"].str.upper() == pnc) &
        ((pninfo2_df["P_START"].isna()) | (pninfo2_df["P_START"] <= p_date)) & 
        ((pninfo2_df["P_END"].isna()) | (pninfo2_df["P_END"] >= p_date))
    ]

    all_matches = pd.concat([matches_pninfo, matches_pninfo2], keys=["PNINFO", "PNINFO2"])

    if not all_matches.empty:
        print("\n✅ Matching PART_NO(s) found:")
        part_nos = []
        for _, row in all_matches.iterrows():
            print(f"🔹 PART_NO: {row['PART_NO']} (From {row.name[0]})")
            part_nos.append(row["PART_NO"])
        return part_nos
    else:
        print("❌ No matching part found.")
        return None

def get_pnc_from_part_no(part_no):
    """Helper function to get PNC from a PART_NO"""
    pninfo_match = pninfo_df[pninfo_df["PART_NO"] == part_no]
    pninfo2_match = pninfo2_df[pninfo2_df["PART_NO"] == part_no]
    
    if not pninfo_match.empty:
        return pninfo_match.iloc[0]["PNC"]
    elif not pninfo2_match.empty:
        return pninfo2_match.iloc[0]["PNC"]
    return None

def suggest_alternative_parts(pnc):
    """Function to suggest alternative parts based on PNC prefix"""
    if not pnc:
        return None
        
    # Get first 4 digits of PNC
    pnc_prefix = pnc[:4]
    
    # Ensure PNC column is string type
    ensure_string_columns(pnc_name_df, ["PNC"])
    
    # Find all parts with same PNC prefix
    similar_parts = pnc_name_df[pnc_name_df["PNC"].str.startswith(pnc_prefix)]
    
    if not similar_parts.empty:
        print(f"\n📋 Available parts in category {pnc_prefix}:")
        for idx, row in similar_parts.iterrows():
            print(f"\n🔹 Description: {row['DESC_ENG']}")
            print(f"  ↳ PNC: {row['PNC']}")
        
        return True
    else:
        print(f"\n❌ No alternative parts found with prefix {pnc_prefix}")
        return False

def filter_by_model_d(part_nos):
    if not part_nos or len(part_nos) == 0:
        print("❌ No PART_NO found to check MODEL_D.")
        return

    results = []
    for part_no in part_nos:
        # First check in PNINFO for MODELD
        pninfo_match = pninfo_df[pninfo_df["PART_NO"] == part_no]
        if not pninfo_match.empty and "MODELD" in pninfo_match.columns:
            modeld_value = pninfo_match.iloc[0]["MODELD"]
            # Then look up this MODELD in MODEL_D.csv
            model_d_match = model_d_df[model_d_df["MODELD"] == modeld_value]
            if not model_d_match.empty:
                results.append({
                    "PART_NO": part_no,
                    "Initial_MODELD": modeld_value,
                    "Final_MODEL_D": model_d_match.iloc[0]["MODEL_D"]
                })

    if results:
        print("\n📌 Cross-Referenced Part Numbers:")
        for result in results:
            print(f"\n🔹 Original PART_NO: {result['PART_NO']}")
            print(f"  ↳ MODELD: {result['Initial_MODELD']}")
            print(f"  ↳ Final MODEL_D: {result['Final_MODEL_D']}")
    else:
        print("\n⚠ No MODEL_D cross-references found for these parts.")

def process_part_lookup_result(part_nos, s_code=None, p_date=None):
    """Function to process lookup results and handle alternative suggestions"""
    if not part_nos:
        return
        
    filter_by_model_d(part_nos)
    
    # Ask if this was the needed part
    found_correct_part = input("\nWas this the PART_NO you were looking for? (y/n): ").strip().lower()
    
    if found_correct_part == 'y':
        print("\n✅ Great! Lookup completed successfully.")
        return True
    
    # If not the right part, suggest alternatives
    print("\nLet me suggest some alternative parts...")
    
    # Get PNC from the first part number
    original_pnc = get_pnc_from_part_no(part_nos[0])
    if original_pnc:
        found_alternatives = suggest_alternative_parts(original_pnc)
        
        if found_alternatives:
            # Ask if they want to search with a new PNC
            search_new = input("\nWould you like to search using one of these alternatives? (y/n): ").strip().lower()
            if search_new == 'y':
                new_pnc = input("\nEnter the PNC you want to search with: ").strip().upper()
                if s_code and p_date:
                    new_part_nos = get_part_no(s_code, p_date, new_pnc)
                    if new_part_nos:
                        process_part_lookup_result(new_part_nos, s_code, p_date)
    
    return False

def main():
    print("\n🔹 WELCOME TO THE AI FORKLIFT PARTS SEARCH 🔹\n")
    
    # Add debug info about environment
    print(f"Supabase URL configured: {'Yes' if SUPABASE_URL else 'No'}")
    print(f"Supabase Key configured: {'Yes' if SUPABASE_KEY else 'No (length: 0)'}")
    
    while True:
        print("\nChoose search method:")
        print("1. Search by M_CODE and part type")
        print("2. Direct PART_NO lookup")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            s_code, p_date = get_s_code_and_p_date()
            if not s_code or not p_date:
                continue

            pnc = get_pnc()
            if not pnc:
                continue

            part_nos = get_part_no(s_code, p_date, pnc)
            if not part_nos:
                continue

            process_part_lookup_result(part_nos, s_code, p_date)
            
        elif choice == "2":
            part_no = input("\nEnter PART_NO to look up: ").strip().upper()
            process_part_lookup_result([part_no])
            
        elif choice == "3":
            print("\n👋 Thank you for using the AI Forklift Parts Search!")
            break
            
        else:
            print("\n❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
