
import streamlit as st
import pandas as pd
import csv
from pathlib import Path

# ============================================================
# 1. KONFIGURASI HALAMAN
# ============================================================

st.set_page_config(
    page_title="Sistem Pakar Kedelai",
    page_icon="🌱",
    layout="wide"
)

# ============================================================
# 2. MEMBACA DATABASE CSV DENGAN HEADER BERULANG
# ============================================================

@st.cache_data
def baca_database():

    file_csv = Path(__file__).parent / "db_sistem_pakar_kedelai.csv"

    bagian = {
        ("kode_aturan", "kode_penyakit"): [],
        ("kode_aturan", "kode_gejala"): [],
        ("kode_gejala", "nama_gejala"): [],
        ("kode_penyakit", "nama_penyakit"): []
    }

    bagian_aktif = None

    with open(file_csv, "r", encoding="utf-8-sig", newline="") as file:
        pembaca = csv.reader(file)

        for baris in pembaca:

            if len(baris) < 2:
                continue

            kolom = (baris[0].strip(), baris[1].strip())

            # Mengenali header setiap bagian CSV
            if kolom in bagian:
                bagian_aktif = kolom
                continue

            # Memasukkan data ke bagian yang sesuai
            if bagian_aktif is not None:
                bagian[bagian_aktif].append(kolom)

    # Membentuk DataFrame
    aturan_penyakit = pd.DataFrame(
        bagian[("kode_aturan", "kode_penyakit")],
        columns=["kode_aturan", "kode_penyakit"]
    )

    aturan_gejala = pd.DataFrame(
        bagian[("kode_aturan", "kode_gejala")],
        columns=["kode_aturan", "kode_gejala"]
    )

    gejala = pd.DataFrame(
        bagian[("kode_gejala", "nama_gejala")],
        columns=["kode_gejala", "nama_gejala"]
    )

    penyakit = pd.DataFrame(
        bagian[("kode_penyakit", "nama_penyakit")],
        columns=["kode_penyakit", "nama_penyakit"]
    )

    # Validasi database
    if any(tabel.empty for tabel in [
        aturan_penyakit,
        aturan_gejala,
        gejala,
        penyakit
    ]):
        raise ValueError(
            "Salah satu bagian database CSV kosong atau tidak terbaca."
        )

    # Mengurutkan kode gejala
    gejala = gejala.sort_values(
        by="kode_gejala"
    ).reset_index(drop=True)

    return aturan_penyakit, aturan_gejala, gejala, penyakit


# Membaca database
try:

    aturan_penyakit, aturan_gejala, gejala, penyakit = baca_database()

except Exception as e:

    st.error(f"Gagal membaca database CSV: {e}")
    st.stop()


# ============================================================
# 3. MEMBENTUK BASIS ATURAN
# ============================================================

basis_aturan = []

for _, baris in aturan_penyakit.iterrows():

    kode_rule = baris["kode_aturan"]
    kode_penyakit = baris["kode_penyakit"]

    # Mengambil kode gejala berdasarkan aturan
    daftar_kode_gejala = aturan_gejala[
        aturan_gejala["kode_aturan"] == kode_rule
    ]["kode_gejala"].tolist()

    # Mengambil nama penyakit
    data_penyakit = penyakit[
        penyakit["kode_penyakit"] == kode_penyakit
    ]

    if data_penyakit.empty:
        continue

    nama_penyakit = data_penyakit.iloc[0]["nama_penyakit"]

    basis_aturan.append({
        "kode_aturan": kode_rule,
        "kode_penyakit": kode_penyakit,
        "nama_penyakit": nama_penyakit,
        "gejala": daftar_kode_gejala
    })


# ============================================================
# 4. TAMPILAN UTAMA
# ============================================================

st.title("🌱 Sistem Pakar Diagnosis Tanaman Kedelai")

st.markdown("""
Aplikasi ini digunakan untuk membantu mengidentifikasi
hama dan penyakit pada tanaman kedelai berdasarkan gejala
yang ditemukan.

Sistem menggunakan metode **Forward Chaining** untuk
mencocokkan gejala dengan aturan diagnosis yang tersedia.
""")

st.divider()


# ============================================================
# 5. INFORMASI DATABASE
# ============================================================

st.subheader("Informasi Basis Pengetahuan")

col1, col2, col3 = st.columns(3)

col1.metric("Data Penyakit", len(penyakit))
col2.metric("Data Gejala", len(gejala))
col3.metric("Basis Aturan", len(basis_aturan))

st.divider()




# ============================================================
# 6. INPUT GEJALA BERDASARKAN KODE - DUA SISI
# ============================================================

st.subheader("Input Gejala Tanaman Kedelai")

st.write(
    "Pilih gejala yang ditemukan pada tanaman kedelai "
    "berdasarkan kode gejala berikut."
)

# Menampung kode gejala yang dipilih
kode_gejala_terpilih = []

# Mengurutkan kode gejala secara numerik
gejala_urut = gejala.copy()

gejala_urut["nomor"] = (
    gejala_urut["kode_gejala"]
    .str.extract(r"(\d+)")
    .astype(int)
)

gejala_urut = gejala_urut.sort_values("nomor")

# Membagi menjadi dua kolom
kolom_kiri, kolom_kanan = st.columns(2)

# Membagi 26 gejala menjadi dua kelompok
setengah = (len(gejala_urut) + 1) // 2

gejala_kiri = gejala_urut.iloc[:setengah]
gejala_kanan = gejala_urut.iloc[setengah:]

# SISI KIRI: G1 - G13
with kolom_kiri:

    for _, baris in gejala_kiri.iterrows():

        kode = baris["kode_gejala"]
        nama = baris["nama_gejala"]

        pilihan = st.checkbox(
            f"{kode} - {nama}",
            key=f"gejala_{kode}"
        )

        if pilihan:
            kode_gejala_terpilih.append(kode)


# SISI KANAN: G14 - G26
with kolom_kanan:


    for _, baris in gejala_kanan.iterrows():

        kode = baris["kode_gejala"]
        nama = baris["nama_gejala"]

        pilihan = st.checkbox(
            f"{kode} - {nama}",
            key=f"gejala_{kode}"
        )

        if pilihan:
            kode_gejala_terpilih.append(kode)


# Mengurutkan kode yang dipilih
kode_gejala_terpilih = sorted(
    kode_gejala_terpilih,
    key=lambda x: int(x[1:])
)

st.divider()

# Ringkasan gejala
st.subheader("Ringkasan Gejala yang Dipilih")

st.metric(
    "Jumlah Gejala Dipilih",
    len(kode_gejala_terpilih)
)

if kode_gejala_terpilih:

    st.success(
        "Kode gejala terpilih: "
        + ", ".join(kode_gejala_terpilih)
    )

else:

    st.warning("Belum ada gejala yang dipilih.")



# ============================================================
# 7. PROSES DIAGNOSIS FORWARD CHAINING
# ============================================================

st.divider()

if st.button(
    "🔍 PROSES DIAGNOSIS",
    type="primary",
    use_container_width=True
):

    if not kode_gejala_terpilih:

        st.warning(
            "Silakan pilih minimal satu gejala sebelum melakukan diagnosis."
        )

    else:

        hasil = []
        kecocokan = []

        # Mengubah pilihan menjadi set
        fakta = set(kode_gejala_terpilih)

        # Memeriksa seluruh aturan
        for rule in basis_aturan:

            gejala_rule = set(rule["gejala"])

            # Menghitung gejala yang cocok
            gejala_cocok = gejala_rule.intersection(fakta)

            # Forward Chaining:
            # Semua gejala dalam aturan harus terpenuhi
            if gejala_rule.issubset(fakta):

                hasil.append(rule)

            # Menghitung aturan yang paling mendekati
            kecocokan.append({
                "rule": rule,
                "cocok": len(gejala_cocok),
                "total": len(gejala_rule),
                "belum": gejala_rule - fakta
            })

        st.divider()
        st.subheader("Hasil Diagnosis")


        # ====================================================
        # 8. MENAMPILKAN HASIL DIAGNOSIS
        # ====================================================

        if hasil:

            st.success(
                f"Ditemukan {len(hasil)} diagnosis "
                "berdasarkan aturan Forward Chaining."
            )

            for nomor, hasil_rule in enumerate(hasil, 1):

                st.markdown(
                    f"### {nomor}. {hasil_rule['nama_penyakit']}"
                )

                col1, col2 = st.columns(2)

                col1.metric(
                    "Kode Penyakit",
                    hasil_rule["kode_penyakit"]
                )

                col2.metric(
                    "Kode Aturan",
                    hasil_rule["kode_aturan"]
                )

                st.write("**Gejala yang memenuhi aturan:**")

                data_gejala_hasil = gejala[
                    gejala["kode_gejala"].isin(
                        hasil_rule["gejala"]
                    )
                ]

                st.dataframe(
                    data_gejala_hasil,
                    use_container_width=True,
                    hide_index=True
                )

                st.divider()

            st.info("""
            Diagnosis diperoleh karena seluruh gejala
            yang menjadi syarat pada aturan telah terpenuhi.
            """)


        # ====================================================
        # 9. JIKA BELUM ADA ATURAN YANG TERPENUHI
        # ====================================================

        else:

            st.warning("""
            Belum ditemukan diagnosis yang memenuhi
            seluruh gejala pada aturan.
            """)

            # Mengurutkan aturan berdasarkan tingkat kecocokan
            kecocokan.sort(
                key=lambda x: (
                    x["cocok"] / x["total"]
                    if x["total"] > 0 else 0
                ),
                reverse=True
            )

            terbaik = kecocokan[0]

            st.markdown("### Pemeriksaan Aturan Terdekat")

            st.write(
                f"**Penyakit:** {terbaik['rule']['nama_penyakit']}"
            )

            st.write(
                f"**Kode penyakit:** "
                f"{terbaik['rule']['kode_penyakit']}"
            )

            st.write(
                f"**Kode aturan:** "
                f"{terbaik['rule']['kode_aturan']}"
            )

            st.write(
                f"**Gejala cocok:** {terbaik['cocok']} "
                f"dari {terbaik['total']} gejala."
            )

            st.write("**Gejala yang belum dipilih:**")

            if terbaik["belum"]:

                data_belum = gejala[
                    gejala["kode_gejala"].isin(
                        terbaik["belum"]
                    )
                ]

                st.dataframe(
                    data_belum,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.write("Tidak ada gejala yang kurang.")

            st.caption(
                "Aturan terdekat hanya menunjukkan tingkat kecocokan "
                "gejala dan bukan probabilitas diagnosis."
            )


# ============================================================
# 10. INFORMASI SISTEM
# ============================================================

with st.expander("Tentang Sistem dan Metode Forward Chaining"):

    st.write("""
    **Forward Chaining** merupakan metode penalaran yang dimulai
    dari fakta atau gejala yang diberikan oleh pengguna.

    Tahapan proses sistem:

    1. Pengguna memilih gejala berdasarkan kode G1 sampai G26.
    2. Sistem menyimpan kode gejala yang dipilih sebagai fakta.
    3. Sistem mencocokkan fakta dengan basis aturan R1 sampai R10.
    4. Jika seluruh gejala pada suatu aturan terpenuhi,
       aturan tersebut menghasilkan kesimpulan berupa penyakit.
    5. Sistem menampilkan hasil diagnosis berdasarkan aturan
       yang berhasil dipenuhi.

    Diagnosis hanya dinyatakan jika seluruh gejala pada aturan
    terpenuhi. Jika belum terpenuhi, sistem menampilkan aturan
    terdekat sebagai informasi tambahan.
    """)


# ============================================================
# 11. FOOTER
# ============================================================

st.divider()

st.caption(
    "Sistem Pakar Diagnosis Hama dan Penyakit Tanaman Kedelai"
)
