
# ============================================================
# SISTEM PAKAR DIAGNOSIS HAMA DAN PENYAKIT TANAMAN KEDELAI
# METODE FORWARD CHAINING
# STREAMLIT + MYSQL
# ============================================================

import streamlit as st
import mysql.connector
import pandas as pd

# ============================================================
# 1. KONFIGURASI HALAMAN STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Sistem Pakar Kedelai",
    page_icon="🌱",
    layout="wide"
)

# ============================================================
# 2. JUDUL APLIKASI
# ============================================================

st.title("🌱 Sistem Pakar Diagnosis Tanaman Kedelai")
st.subheader("Diagnosis Hama dan Penyakit Menggunakan Forward Chaining")

st.write(
    "Aplikasi ini digunakan untuk membantu mendiagnosis "
    "hama dan penyakit pada tanaman kedelai berdasarkan "
    "gejala yang dipilih pengguna."
)

st.divider()

# ============================================================
# 3. KONEKSI DATABASE MYSQL
# ============================================================

# SESUAIKAN KONFIGURASI INI DENGAN MYSQL KAMU

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "root"
DB_NAME = "db_sistem_pakar_kedelai"


@st.cache_resource
def koneksi_database():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        port=int(st.secrets["mysql"]["port"]),
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"]
    )


# ============================================================
# 4. MEMBACA DATA GEJALA DARI DATABASE
# ============================================================

def ambil_gejala():
    db = koneksi_database()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT kode_gejala, nama_gejala
        FROM gejala
        ORDER BY kode_gejala
    """)

    data = cursor.fetchall()
    cursor.close()

    return data


# ============================================================
# 5. MEMBACA DATA ATURAN DARI DATABASE
# ============================================================

def ambil_aturan():
    db = koneksi_database()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            a.kode_aturan,
            p.kode_penyakit,
            p.nama_penyakit,
            ad.kode_gejala,
            g.nama_gejala
        FROM aturan a
        JOIN penyakit p
            ON a.kode_penyakit = p.kode_penyakit
        JOIN aturan_detail ad
            ON a.kode_aturan = ad.kode_aturan
        JOIN gejala g
            ON ad.kode_gejala = g.kode_gejala
        ORDER BY a.kode_aturan, ad.kode_gejala
    """)

    data = cursor.fetchall()
    cursor.close()

    return data


# ============================================================
# 6. PROSES FORWARD CHAINING
# ============================================================

def proses_forward_chaining(gejala_dipilih, data_aturan):

    hasil_diagnosis = []
    kelompok_aturan = {}

    # Mengelompokkan gejala berdasarkan kode aturan
    for baris in data_aturan:

        kode = baris["kode_aturan"]

        if kode not in kelompok_aturan:
            kelompok_aturan[kode] = {
                "kode_penyakit": baris["kode_penyakit"],
                "nama_penyakit": baris["nama_penyakit"],
                "gejala": []
            }

        kelompok_aturan[kode]["gejala"].append(
            baris["kode_gejala"]
        )

    # Memeriksa apakah seluruh gejala dalam aturan terpenuhi
    for kode_aturan, aturan in kelompok_aturan.items():

        gejala_persyaratan = set(aturan["gejala"])

        if gejala_persyaratan.issubset(gejala_dipilih):

            hasil_diagnosis.append({
                "kode_aturan": kode_aturan,
                "kode_penyakit": aturan["kode_penyakit"],
                "nama_penyakit": aturan["nama_penyakit"],
                "gejala_terpenuhi": list(gejala_persyaratan)
            })

    return hasil_diagnosis, kelompok_aturan


# ============================================================
# 7. MENAMPILKAN FORM PILIH GEJALA
# ============================================================

try:

    data_gejala = ambil_gejala()
    data_aturan = ambil_aturan()

    if not data_gejala or not data_aturan:
        st.warning("Data gejala atau aturan belum tersedia di database.")
        st.stop()

    st.header("Pilih Gejala Tanaman Kedelai")

    st.write(
        "Silakan pilih semua gejala yang ditemukan "
        "pada tanaman kedelai."
    )

    # Membuat pilihan gejala
    pilihan_gejala = {
        f'{g["kode_gejala"]} - {g["nama_gejala"]}':
        g["kode_gejala"]
        for g in data_gejala
    }

    with st.form("form_diagnosis"):

        gejala_terpilih = st.multiselect(
            "Pilih gejala yang dialami tanaman:",
            options=list(pilihan_gejala.keys()),
            placeholder="Klik untuk memilih gejala..."
        )

        tombol_diagnosis = st.form_submit_button(
            "🔍 Proses Diagnosis",
            use_container_width=True
        )

    # ========================================================
    # 8. MENJALANKAN DIAGNOSIS
    # ========================================================

    if tombol_diagnosis:

        if len(gejala_terpilih) == 0:

            st.warning("Silakan pilih minimal satu gejala terlebih dahulu.")

        else:

            kode_gejala_dipilih = {
                pilihan_gejala[g]
                for g in gejala_terpilih
            }

            hasil, semua_aturan = proses_forward_chaining(
                kode_gejala_dipilih,
                data_aturan
            )

            st.divider()
            st.header("Hasil Diagnosis")

            # Menampilkan gejala yang dipilih
            st.subheader("Gejala yang Dipilih")

            for g in gejala_terpilih:
                st.write("✓", g)

            st.divider()

            # =================================================
            # 9. HASIL JIKA ATURAN TERPENUHI
            # =================================================

            if hasil:

                st.success("Aturan Forward Chaining berhasil terpenuhi!")

                for nomor, diagnosis in enumerate(hasil, start=1):

                    st.subheader(f"Hasil Diagnosis {nomor}")

                    st.markdown(
                        f"**Kode Penyakit:** "
                        f"{diagnosis['kode_penyakit']}"
                    )

                    st.markdown(
                        f"**Nama Penyakit:** "
                        f"{diagnosis['nama_penyakit']}"
                    )

                    st.markdown(
                        f"**Aturan Terpenuhi:** "
                        f"{diagnosis['kode_aturan']}"
                    )

                    st.write("Gejala yang memenuhi aturan:")

                    for kode in diagnosis["gejala_terpenuhi"]:
                        nama = next(
                            (
                                g["nama_gejala"]
                                for g in data_gejala
                                if g["kode_gejala"] == kode
                            ),
                            kode
                        )
                        st.write(f"- {kode}: {nama}")

                    st.divider()

                st.info(
                    "Diagnosis diperoleh karena seluruh gejala "
                    "yang menjadi syarat pada aturan telah terpenuhi."
                )

            # =================================================
            # 10. JIKA TIDAK ADA ATURAN YANG TERPENUHI
            # =================================================

            else:

                st.error(
                    "Belum ditemukan penyakit yang sesuai "
                    "dengan seluruh gejala yang dipilih."
                )

                st.subheader("Analisis Kecocokan Aturan")

                # Menghitung aturan yang paling mendekati
                analisis = []

                for kode, aturan in semua_aturan.items():

                    syarat = set(aturan["gejala"])
                    cocok = syarat.intersection(
                        kode_gejala_dipilih
                    )

                    persentase = (
                        len(cocok) / len(syarat)
                    ) * 100

                    analisis.append({
                        "Kode Aturan": kode,
                        "Nama Penyakit": aturan["nama_penyakit"],
                        "Gejala Terpenuhi": f"{len(cocok)}/{len(syarat)}",
                        "Kecocokan": f"{persentase:.0f}%"
                    })

                df_analisis = pd.DataFrame(analisis)

                st.dataframe(
                    df_analisis.sort_values(
                        by="Kecocokan",
                        ascending=False
                    ),
                    use_container_width=True,
                    hide_index=True
                )

                st.caption(
                    "Persentase di atas hanya menunjukkan jumlah gejala "
                    "yang cocok dengan aturan, bukan probabilitas penyakit "
                    "dan bukan hasil diagnosis."
                )

except mysql.connector.Error as e:

    st.error("Gagal menghubungkan ke database MySQL.")

    st.code(str(e))

    st.info(
        "Periksa apakah MySQL sudah aktif, nama database benar, "
        "dan konfigurasi username serta password sudah sesuai."
    )

except Exception as e:

    st.error("Terjadi kesalahan pada aplikasi.")
    st.code(str(e))


# ============================================================
# 11. INFORMASI METODE
# ============================================================

st.divider()

st.caption(
    "Sistem Pakar Tanaman Kedelai | "
    "Metode Forward Chaining | "
    "Database MySQL"
)
