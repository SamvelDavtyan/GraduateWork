import datetime as datetime
from flask_login import UserMixin
from sqlalchemy import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

from config import database


class Role:
    STUDENT = "Студент"
    TEACHER = "Преподаватель"

    @staticmethod
    def get_roles():
        return [Role.STUDENT, Role.TEACHER]

    @staticmethod
    def get_role(role):
        if role is not None and role == Role.TEACHER:
            return Role.TEACHER
        else:
            return Role.STUDENT


class User(database.Model, UserMixin):
    __tablename__ = "user"
    id = Column(Integer(), primary_key=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    middle_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False, default=Role.STUDENT)
    group_id = Column(String(), ForeignKey("group.id"))
    point_data_list = relationship("PointData", backref="user")
    remarks = relationship("Remark", backref="user")

    def get_my_statements(self):
        my_statements = []
        for statement in get_all(Statement):
            if self.group in statement.groups:
                my_statements.append(statement)
        return my_statements

    def __str__(self):
        return self.get_full_name()

    def is_teacher(self):
        return self.role == Role.TEACHER

    def get_full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Subject(database.Model):
    __tablename__ = "subject"
    id = Column(Integer(), primary_key=True)
    name = Column(String(), unique=True, nullable=False)
    statements = relationship("Statement", backref="subject")


class Group(database.Model):
    __tablename__ = "group"
    id = Column(Integer(), primary_key=True)
    name = Column(String(), unique=True)
    students = relationship("User", backref="group")

    def get_students_with_sort(self):
        temp = self.students
        temp.sort(key=lambda x: x.get_full_name())
        return temp

    def __str__(self):
        return self.name


group_statement = database.Table("group_statement",
                                 database.Column("group_id", database.Integer, database.ForeignKey("group.id")),
                                 database.Column("statement_id", database.Integer, database.ForeignKey("statement.id"))
                                 )


class Statement(database.Model):
    __tablename__ = "statement"
    id = Column(Integer(), primary_key=True)
    year = Column(Integer(), nullable=True)
    semester = Column(Integer(), nullable=True)
    subject_id = Column(String(), ForeignKey("subject.id"), nullable=False)
    groups = database.relationship("Group", secondary=group_statement, backref="statement")
    points = relationship("Point", backref="statement")

    def __str__(self):
        return f"{self.subject.name}, {self.year}/{self.semester}, {self.get_groups_str()},"

    def get_groups_str(self):
        if len(self.groups) == 0:
            return "Группы не добавлены"
        return_str = ""
        for group in self.groups:
            return_str += group.name + ", "
        return_str = return_str.rstrip(", ")
        return return_str


class Point(database.Model):
    __tablename__ = "point"
    id = Column(Integer(), primary_key=True)
    name = Column(String(255), nullable=False)
    point_data_list = relationship("PointData", backref="point")
    statement_id = Column(String(), ForeignKey("statement.id"))

    def find_point_data_by_user_id(self, user_id):
        for point_data in self.point_data_list:
            if point_data.user.id == user_id:
                return point_data


class PointData(database.Model):
    __tablename__ = "point_data"
    id = Column(Integer(), primary_key=True)
    program_grade = Column(String(), nullable=True)
    report_grade = Column(String(), nullable=True)
    point_id = Column(String(), ForeignKey("point.id"), nullable=False)
    user_id = Column(String(), ForeignKey("user.id"), nullable=False)
    remarks = relationship("Remark", backref="point_data")
    programs = relationship("Program", backref="point_data")
    reports = relationship("Report", backref="point_data")

    def get_last_program(self):
        if len(self.programs) > 0:
            programs = self.programs
            programs = sorted(programs, key=lambda x: x.datetime, reverse=True)
            return programs[0]
        else:
            return None

    def get_last_report(self):
        if len(self.reports) > 0:
            reports = self.reports
            reports = sorted(reports, key=lambda x: x.datetime, reverse=True)
            return reports[0]
        else:
            return None


class PointDataStatus:
    ACCEPTED = "Принято"
    DECLINED = "Отклонено"
    PENDING = "Есть замечания"
    NEW = "Новый"


class Program(database.Model):
    __tablename__ = "program"
    id = Column(Integer(), primary_key=True)
    datetime = Column(String(), nullable=False)
    filename = Column(String(), nullable=True)
    point_data_id = Column(String(), ForeignKey("point_data.id"), nullable=False)
    # status = Column(String(), nullable=False, default=PointDataStatus.PENDING)
    status = Column(String(), nullable=False, default=PointDataStatus.NEW)

    def get_bg_style(self):
        if self.status == PointDataStatus.ACCEPTED:
            return "bg-success"
        if self.status == PointDataStatus.DECLINED:
            return "bg-danger"
        if self.status == PointDataStatus.PENDING:
            return "bg-warning"
        if self.status == PointDataStatus.NEW:
            return "bg-info"


class Report(database.Model):
    __tablename__ = "report"
    id = Column(Integer(), primary_key=True)
    datetime = Column(String(), nullable=False)
    filename = Column(String(), nullable=True)
    point_data_id = Column(String(), ForeignKey("point_data.id"), nullable=False)
    status = Column(String(), nullable=False, default=PointDataStatus.NEW)

    def get_bg_style(self):
        if self.status == PointDataStatus.ACCEPTED:
            return "bg-success"
        if self.status == PointDataStatus.DECLINED:
            return "bg-danger"
        if self.status == PointDataStatus.PENDING:
            return "bg-warning"
        if self.status == PointDataStatus.NEW:
            return "bg-info"


class RemarkType:
    PROGRAM_REMARK = "PROGRAM"
    REPORT_REMARK = "REPORT"


class Remark(database.Model):
    __tablename__ = "remark"
    id = Column(Integer(), primary_key=True)
    text = Column(String(), nullable=False)
    datetime = Column(DateTime(), nullable=False)
    point_data_id = Column(String(), ForeignKey("point_data.id"))
    type = Column(String(), nullable=False)
    author_id = Column(String(), ForeignKey("user.id"), nullable=False)

    def is_program_remark(self):
        return self.type == RemarkType.PROGRAM_REMARK

    def is_report_remark(self):
        return self.type == RemarkType.REPORT_REMARK

    def get_datetime_format_str(self):
        return self.datetime.strftime('%Y-%m-%d %H:%M')


def save(obj):
    try:
        database.session.add(obj)
        database.session.commit()
    except SQLAlchemyError as e:
        print(e)
        database.session.rollback()


def delete_all(obj_clas):
    database.session.query(obj_clas).delete()
    database.session.commit()


def delete(obj):
    database.session.delete(obj)
    database.session.commit()


def get_all(obj_class):
    return database.session.query(obj_class).all()


def find_by_id(obj_class, obj_id):
    return database.session.query(obj_class).filter(obj_class.id == obj_id).first()
