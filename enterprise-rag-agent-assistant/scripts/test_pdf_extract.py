from app.services.document_service import read_pdf_text


def main() -> None:
    file_path = "data/sample_docs/company_policy.pdf"

    text = read_pdf_text(file_path)

    print("PDF text length:", len(text))
    print("\n--- PDF text preview ---")
    print(text[:1000])


if __name__ == "__main__":
    main()