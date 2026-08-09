import sys, json

def riset_niche(query):
    # Simulasi panggil Asisten Jun untuk riset niche global
    print(f"--- Melakukan riset niche global untuk: {query} ---")
    print("Top Global Niche: AI Prompt Engineering for Small Businesses (High Demand)")
    print("Pain: AI is hard to customize.")
    print("Gain: Custom business prompts increase efficiency by 80%.")
    print("Language: English.")

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "digital products"
    riset_niche(query)
