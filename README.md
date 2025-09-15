# YouTube Comments Collector

Aplikasi Python dengan Streamlit yang terintegrasi dengan YouTube API v3 dan Supabase untuk mengumpulkan komentar YouTube.

## Fitur

- ✅ Ekstrak video ID dari link YouTube
- ✅ Validasi video ID di database Supabase
- ✅ Ambil seluruh komentar menggunakan YouTube API v3 dengan pagination
- ✅ Simpan komentar ke database Supabase
- ✅ Tampilkan komentar dalam tabel scrollable
- ✅ Download komentar dalam format CSV
- ✅ Statistik database (total video dan komentar)

## Prerequisites

1. **YouTube API Key**: Aktif YouTube Data API v3 di Google Cloud Console
2. **Supabase Account**: Database PostgreSQL di Supabase
3. **Python 3.7+**

## Instalasi

1. Clone atau download project ini
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Setup database Supabase:
   - Buka Supabase Dashboard
   - Masuk ke SQL Editor
   - Jalankan script dari file `supabase_tables.sql`

4. Konfigurasi environment variables:
   - Edit file `.env` dengan API keys Anda
   - Atau set environment variables di sistem

## Struktur Database

### Tabel `youtube_videos`
```sql
CREATE TABLE youtube_videos (
    video_id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Tabel `youtube_comments`
```sql
CREATE TABLE youtube_comments (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    author_name TEXT NOT NULL,
    comment_text TEXT NOT NULL,
    inserted_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Menjalankan Aplikasi

```bash
streamlit run app.py
```

Aplikasi akan berjalan di `http://localhost:8501`

## Cara Penggunaan

1. **Input YouTube Link**:
   - Masukkan link YouTube video
   - Klik tombol "Ambil Komentar"

2. **Proses Otomatis**:
   - Ekstrak video ID dari link
   - Validasi apakah video sudah pernah diproses
   - Ambil judul video dari YouTube API
   - Ambil semua komentar dengan pagination
   - Simpan ke database Supabase

3. **Output**:
   - Judul video
   - Jumlah total komentar
   - Tabel scrollable berisi semua komentar
   - Opsi download CSV

## Format Link YouTube yang Didukung

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- `https://www.youtube.com/v/VIDEO_ID`

## Batasan

- Video harus memiliki komentar yang dapat diakses publik
- Rate limit YouTube API: 10,000 requests per hari (default)
- Supabase: Batch insert 1000 records per request

## Error Handling

- ❌ Link YouTube tidak valid
- ⚠️ Video sudah pernah diproses
- ❌ Komentar dinonaktifkan atau video privat
- ❌ API quota exceeded
- ❌ Network/database connection issues

## Dependencies

- `streamlit`: Web framework untuk UI
- `google-api-python-client`: YouTube API v3 client
- `supabase`: Supabase Python client
- `python-dotenv`: Environment variables
- `pandas`: Data manipulation dan CSV export

## API Configuration

File `.env`:
```
YOUTUBE_API_KEY=your_youtube_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

## Troubleshooting

### YouTube API Errors
- Pastikan API key valid dan YouTube Data API v3 enabled
- Check quota limits di Google Cloud Console

### Supabase Errors
- Pastikan database tables sudah dibuat
- Check service role key permissions
- Verify network connectivity

### Streamlit Issues
- Update Streamlit ke versi terbaru
- Clear browser cache
- Check Python version compatibility

## License

MIT License - Silakan digunakan dan dimodifikasi sesuai kebutuhan.
