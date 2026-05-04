from io import BytesIO
import hashlib
import os

import gridfs.errors
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas

ICON_PATH = "/Users/arvinazad/Desktop/Hofstra/Brochadia/brochadia/src/assets/brochadia_ico.jpg"
EXCLUDED_RESUME_FIELDS = {
    "Trip_id",
    "_id",
    "password",
    "files",
    "trip_history",
    "travel_history",
    "travel_preference",
    "location_preference",
    "Past_Trips_ID",
    "Saved_Trips_ID",
    ""
}


def _calculate_hash(content):
    md5 = hashlib.md5()
    md5.update(content)
    return md5.hexdigest()


def _format_key(key):
    key = str(key or "").replace("_", " ").strip()
    return key[:1].upper() + key[1:] if key else ""


def _stringify_value(value):
    if value in (None, ""):
        return ""

    if isinstance(value, dict):
        parts = []
        for key, nested_value in value.items():
            nested_text = _stringify_value(nested_value)
            if nested_text:
                parts.append(f"{_format_key(key)}: {nested_text}")
        return ", ".join(parts)

    if isinstance(value, list):
        parts = []
        for item in value:
            item_text = _stringify_value(item)
            if item_text:
                parts.append(item_text)
        return ", ".join(parts)

    return str(value)


def _draw_page_header(canvas, data, width, height):
    if os.path.exists(ICON_PATH):
        canvas.drawImage(ICON_PATH, x=width - 60, y=height - 60, width=40, height=40)

    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawCentredString(
        width / 2.0,
        height - 60,
        f"Travel Resume by {data.get('full_name', 'Unknown User')}",
    )
    return height - 95


def _ensure_space(canvas, y_position, required_space, data, width, height):
    if y_position >= required_space:
        return y_position

    canvas.showPage()
    return _draw_page_header(canvas, data, width, height)


def _draw_wrapped_text(canvas, text, x_position, y_position, max_width, line_spacing):
    words = text.split()
    if not words:
        return y_position - line_spacing

    current_line = words[0]
    for word in words[1:]:
        candidate = f"{current_line} {word}"
        if canvas.stringWidth(candidate, "Helvetica", 12) <= max_width:
            current_line = candidate
            continue

        canvas.drawString(x_position, y_position, current_line)
        y_position -= line_spacing
        current_line = word

    canvas.drawString(x_position, y_position, current_line)
    return y_position - line_spacing


def _apply_review_details(data, review_data=None, description=None, rating=None):
    resume_data = dict(data or {})
    history_key = "travel_history" if resume_data.get("travel_history") else "trip_history"
    history = list(resume_data.get(history_key) or [])
    target_trip_id = str((review_data or {}).get("trip_id") or "").strip()
    excluded_trip_fields = {"trip_id", "experiences", "purchased_at", "reviewed_at"}

    if not target_trip_id:
        resume_data[history_key] = history
        return resume_data

    for index, trip in enumerate(history):
        if not isinstance(trip, dict):
            continue

        if str(trip.get("trip_id") or "").strip() != target_trip_id:
            continue

        updated_trip = {
            key: value
            for key, value in trip.items()
            if key not in excluded_trip_fields
        }
        if description:
            updated_trip["review_description"] = description
        if rating is not None:
            updated_trip["review_rating"] = rating

        history[index] = updated_trip
        break

    resume_data[history_key] = history
    return resume_data


def build_resume_pdf(data):
    buffer = BytesIO()
    canvas = Canvas(buffer, pagesize=letter)
    width, height = letter
    x_position = 72
    max_width = width - (x_position * 2)
    line_spacing = 16

    y_position = _draw_page_header(canvas, data, width, height)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(x_position, y_position, "Profile")
    y_position -= 24

    canvas.setFont("Helvetica", 12)
    for key, value in data.items():
        print(key, value)
        if key in EXCLUDED_RESUME_FIELDS:
            continue

        text_value = _stringify_value(value)
        if not text_value:
            continue

        y_position = _ensure_space(canvas, y_position, 90, data, width, height)
        canvas.setFont("Helvetica", 12)
        y_position = _draw_wrapped_text(
            canvas,
            f"{_format_key(key)}: {text_value}",
            x_position,
            y_position,
            max_width,
            line_spacing,
        )

    history = data.get("travel_history") or data.get("trip_history") or []

    y_position = _ensure_space(canvas, y_position, 110, data, width, height)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(x_position, y_position, "Travel History")
    y_position -= 24

    if not history:
        canvas.setFont("Helvetica", 12)
        _draw_wrapped_text(
            canvas,
            "No travel history is available for this user yet.",
            x_position,
            y_position,
            max_width,
            line_spacing,
        )
    else:
        for index, trip in enumerate(history, start=1):
            y_position = _ensure_space(canvas, y_position, 110, data, width, height)
            canvas.setFont("Helvetica-Bold", 12)
            canvas.drawString(x_position, y_position, f"Trip {index}")
            y_position -= 20

            if isinstance(trip, dict):
                trip_items = trip.items()
            else:
                trip_items = [("details", trip)]

            canvas.setFont("Helvetica", 12)
            for key, value in trip_items:
                if key in EXCLUDED_RESUME_FIELDS:
                    continue
                text_value = _stringify_value(value)
                if not text_value:
                    continue

                y_position = _ensure_space(canvas, y_position, 90, data, width, height)
                y_position = _draw_wrapped_text(
                    canvas,
                    f"{_format_key(key)}: {text_value}",
                    x_position + 12,
                    y_position,
                    max_width - 12,
                    line_spacing,
                )

            y_position -= 8

    canvas.save()
    return buffer.getvalue()


def create_Resume(data, fileName, filePath="Desktop/Hofstra/Brochadia/brochadia/src/documents"):
    save_name = os.path.join(os.path.expanduser("~"), filePath, fileName)
    os.makedirs(os.path.dirname(save_name), exist_ok=True)

    pdf_content = build_resume_pdf(data)
    with open(save_name, "wb") as pdf_file:
        pdf_file.write(pdf_content)

    url = f"http://127.0.0.1:5000//upload/{data['_id']}"
    with open(save_name, "rb") as img:
        files = {"file": (fileName, img, "application/pdf")}
        return requests.post(url, files=files)


def modify_resume(
    data,
    obj_id,
    fs,
    file_name="file.pdf",
    filePath="Desktop/Hofstra/Brochadia/brochadia/src/documents",
    review_data=None,
    description=None,
    rating=None,
):
    save_name = os.path.join(os.path.expanduser("~"), filePath, file_name)
    os.makedirs(os.path.dirname(save_name), exist_ok=True)

    resume_data = _apply_review_details(
        data,
        review_data=review_data,
        description=description,
        rating=rating,
    )
    print(resume_data)
    pdf_content = build_resume_pdf(resume_data)
    with open(save_name, "wb") as pdf_file:
        pdf_file.write(pdf_content)

    try:
        fs.delete(obj_id)
    except gridfs.errors.NoFile:
        pass

    fs.put(pdf_content, _id=obj_id, filename=file_name, contentType="application/pdf")
    return {
        "file_id": obj_id,
        "hash": _calculate_hash(pdf_content),
        "path": save_name,
    }
