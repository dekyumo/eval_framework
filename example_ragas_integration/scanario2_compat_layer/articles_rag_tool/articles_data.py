"""Sample news articles used for retrieval evaluation."""

ARTICLES = [
    # Business articles
    {"text": "The stock market reached a new high today, with technology stocks leading the gains.", "category": "Business"},
    {"text": "The government announced a new tax policy that will affect small businesses.", "category": "Business"},
    {"text": "The central bank has decided to keep interest rates unchanged.", "category": "Business"},
    {"text": "Quarterly earnings reports exceeded expectations for most Fortune 500 companies.", "category": "Business"},
    {"text": "Inflation rates have decreased for the third consecutive month.", "category": "Business"},
    {"text": "The merger between two major corporations has been approved by regulators.", "category": "Business"},
    {"text": "Unemployment rates have fallen to a five-year low according to new data.", "category": "Business"},
    {"text": "The cryptocurrency market experienced significant volatility this week.", "category": "Business"},
    # Health articles
    {"text": "A new study shows that regular exercise can reduce the risk of heart disease.", "category": "Health"},
    {"text": "A clinical trial for a new cancer treatment has shown promising results.", "category": "Health"},
    {"text": "A balanced diet and regular sleep are essential for maintaining good health.", "category": "Health"},
    {"text": "Medical researchers have identified a new gene linked to Alzheimer's disease.", "category": "Health"},
    {"text": "The WHO has issued new guidelines for managing diabetes in elderly patients.", "category": "Health"},
    {"text": "A new technique for early detection of breast cancer has been developed.", "category": "Health"},
    {"text": "Studies show that mindfulness meditation can help reduce stress and anxiety.", "category": "Health"},
    {"text": "Public health officials warn of a potential flu outbreak this winter season.", "category": "Health"},
    # Technology articles
    {"text": "The latest smartphone from Apple features a better camera and longer battery life.", "category": "Technology"},
    {"text": "The new electric car from Tesla has a range of over 400 miles.", "category": "Technology"},
    {"text": "The latest update to the operating system includes new security features.", "category": "Technology"},
    {"text": "A new artificial intelligence system can detect diseases from medical images.", "category": "Technology"},
    {"text": "The tech company unveiled its new virtual reality headset at the annual conference.", "category": "Technology"},
    {"text": "Researchers have developed a quantum computer that can solve complex problems.", "category": "Technology"},
    {"text": "The new social media platform has gained millions of users in just a few months.", "category": "Technology"},
    {"text": "Cybersecurity experts warn of a new type of malware targeting smart home devices.", "category": "Technology"},
    # Science articles
    {"text": "Scientists have discovered a new species of frog in the Amazon rainforest.", "category": "Science"},
    {"text": "Astronomers have observed a supernova in a distant galaxy.", "category": "Science"},
    {"text": "Researchers have developed a new method for measuring ocean temperatures.", "category": "Science"},
    {"text": "A fossil discovery suggests that dinosaurs may have been warm-blooded.", "category": "Science"},
    {"text": "Climate scientists report that Arctic ice is melting at an unprecedented rate.", "category": "Science"},
    {"text": "Physicists have confirmed the existence of a new subatomic particle.", "category": "Science"},
    {"text": "A study of coral reefs shows signs of recovery in protected marine areas.", "category": "Science"},
    {"text": "Biologists have sequenced the genome of an endangered species of tiger.", "category": "Science"},
]

DEMO_QUERY = "What decision did the central bank make about interest rates?"
DEMO_REFERENCE = "The central bank decided to keep interest rates unchanged."
DEMO_REFERENCE_CONTEXT = ARTICLES[2]["text"]
DEMO_REFERENCE_CONTEXT_ID = "article-2"
