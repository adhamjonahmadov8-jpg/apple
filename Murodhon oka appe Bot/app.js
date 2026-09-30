import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getFirestore, collection, onSnapshot, query, orderBy } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js";

// Siz bergan Firebase konfiguratsiyasi
const firebaseConfig = {
  apiKey: "AIzaSyBYuoasNYJ2Pvtk-IglbYe-nCAS8gaMrBg",
  authDomain: "olmastat-bot.firebaseapp.com",
  projectId: "olmastat-bot",
  storageBucket: "olmastat-bot.firebasestorage.app",
  messagingSenderId: "114005126414",
  appId: "1:114005126414:web:f53fde6cbc5f3887683b5f",
  measurementId: "G-3K96B6PZWH"
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

// Jonli ma'lumotlarni Firebase'dan olish
const salesRef = collection(db, "sales");
const q = query(salesRef, orderBy("date", "desc"));

onSnapshot(q, (snapshot) => {
    const tableBody = document.getElementById("sales-table-body");
    tableBody.innerHTML = "";

    let s1 = 0, s2 = 0, s3 = 0;

    snapshot.forEach((doc) => {
        const data = doc.data();
        
        // Hisob-kitoblar
        if (data.apple_sort.includes("1-sort")) s1 += data.quantity;
        else if (data.apple_sort.includes("2-sort")) s2 += data.quantity;
        else if (data.apple_sort.includes("3-sort")) s3 += data.quantity;

        // Jadvalga qator qo'shish
        const row = document.createElement("tr");
        row.className = "border-b border-gray-700/50 hover:bg-gray-750";
        row.innerHTML = `
            <td class="p-3 text-sm">${data.date || '-'}</td>
            <td class="p-3 text-sm font-semibold">${data.user_name || 'Xodim'} (${data.username})</td>
            <td class="p-3 text-sm">${data.apple_sort}</td>
            <td class="p-3 text-sm text-green-400 font-bold">${data.quantity} kg</td>
        `;
        tableBody.appendChild(row);
    });

    // Vidjetlarni yangilash
    document.getElementById("total-sort1").innerText = `${s1} kg`;
    document.getElementById("total-sort2").innerText = `${s2} kg`;
    document.getElementById("total-sort3").innerText = `${s3} kg`;
    document.getElementById("total-all").innerText = `${s1 + s2 + s3} kg`;
});