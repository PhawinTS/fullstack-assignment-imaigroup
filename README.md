📸 Photobooth Application
📝 Project Overview

Photobooth Application เป็นแอปพลิเคชัน Full Stack ที่พัฒนาโดยใช้เทคโนโลยี Next.js, React, FastAPI, ElysiaJS, PostgreSQL, และ Docker โดยมีวัตถุประสงค์เพื่อให้ผู้ใช้สามารถถ่ายภาพ แก้ไข และแชร์ได้อย่างสะดวกสบาย

🛠 Technology Stack

Frontend: Next.js, React

Backend: FastAPI, ElysiaJS (Python)

Database: PostgreSQL

Containerization: Docker

Hosting: DigitalOcean

💾 Setup Instructions
1. Clone Repository
git clone https://github.com/PhawinTS/fullstack-assignment-imaigroup.git
cd fullstack-assignment-imaigroup

2. สร้างไฟล์ .env สำหรับ Backend
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<db_name>
SECRET_KEY=your_secret_key

3. ติดตั้ง Dependencies
Frontend:
cd frontend
npm install

Backend:
cd backend
pip install -r requirements.txt

4. รันโปรเจกต์ในโหมดพัฒนา
Backend:
cd backend
uvicorn main:app --reload

Frontend:
cd frontend
npm run dev


เปิดเบราว์เซอร์และไปที่ http://localhost:3000

🐳 Docker Setup (Optional)
docker-compose up --build

☁️ Deployment (DigitalOcean + Docker)
1. สร้าง Droplet บน DigitalOcean และ SSH เข้าไป
2. ติดตั้ง Docker และ Docker Compose บน Droplet
3. โคลน Repository ไปยัง Droplet:
git clone https://github.com/PhawinTS/fullstack-assignment-imaigroup.git
cd fullstack-assignment-imaigroup

4. สร้างไฟล์ .env สำหรับการตั้งค่าต่าง ๆ:
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<db_name>
SECRET_KEY=your_secret_key

5. สร้างและรัน Docker Compose:
docker-compose up --build -d

📄 API Documentation
Endpoint	Method	Body	Response
/api/photos	GET	-	List all photos
/api/photos	POST	{ "image": <file>, "tags": [] }	Create new photo
/api/photos/:id	GET	-	Get photo by ID
/api/photos/:id	DELETE	-	Delete photo

📬 Contact

Email: thon.pwin@gmail.com
