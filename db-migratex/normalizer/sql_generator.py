# normalizer/sql_generator.py

class SQLGenerator:
    def generate_students_norm_sql(self):
        """
        Example: normalized schema for students.
        """
        create_students = """
        CREATE TABLE IF NOT EXISTS students_norm(
            id INT PRIMARY KEY AUTO_INCREMENT,
            legacy_id VARCHAR(20) UNIQUE,
            name VARCHAR(100),
            age INT,
            department VARCHAR(50)
        );
        """.strip()
        return create_students
