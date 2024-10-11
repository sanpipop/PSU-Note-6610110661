import flask
from flask import request 
import models
import forms


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )


@app.route("/note/edit/<int:note_id>", methods=["GET", "POST"])
def note_edit(note_id):
    db = models.db
    note = db.session.get(models.Note, note_id) # ดึงข้อมูล Note จากฐานข้อมูลด้วย ID
    form = forms.NoteForm(obj=note) # สร้างฟอร์มแล้วใส่ข้อมูลจากโน้ตลงในฟอร์ม
    
    if request.method == 'GET':
        form.tags.data = [tag.name for tag in note.tags] # ตอนเปิดฟอร์มครั้งแรก ให้เติมชื่อแท็กลงใน form.tags.data

    if form.validate_on_submit(): # เมื่อกด Save Change
        # อัปเดตข้อมูลโน้ตจากฟอร์มที่กรอกมา
        note.title = form.title.data
        note.description = form.description.data

        # เช็ค Tags
        new_tags = []
        for tag_name in form.tags.data:
            # ตรวจสอบว่าแต่ละแท็กในฟอร์มมีในฐานข้อมูลแล้วยัง
            tag = db.session.execute(
                db.select(models.Tag).where(models.Tag.name == tag_name)
            ).scalars().first()
            
            # ถ้ายังไม่มีแท็กนี้ก็สร้างขึ้นมาใหม่
            if not tag:
                tag = models.Tag(name=tag_name)
                db.session.add(tag)  # เพิ่ม tag ใหม่ลงไป 
            
            new_tags.append(tag)  # เพิ่ม tag ที่ได้เข้าไปใน new_tags

        # แทนที่แท็กเก่าของโน้ตด้วยลิสของแท็กใหม่
        note.tags = new_tags
        
        # บันทึกการเปลี่ยนแปลงลงฐานข้อมูล
        db.session.commit()

        # บันทึกเสร็จแล้วก็กลับไปหน้าแรก
        return flask.redirect(flask.url_for("index"))

    return flask.render_template("edit.html", form=form)


@app.route("/note/delete/<int:note_id>", methods=["POST"])
def note_delete(note_id):
    db = models.db
    note = db.session.get(models.Note, note_id)  #  หาโน้ตจาก ID
    
    if note:
        db.session.delete(note)  # ลบโน้ต
        db.session.commit() 
    return flask.redirect(flask.url_for("index"))  # ทำงานเสร็จก็กลับไปหน้าแรก


if __name__ == "__main__":
    app.run(debug=True)



