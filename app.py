import streamlit as st
import re
import os
import requests
from datetime import datetime
import pandas as pd
from googleapiclient.discovery import build
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration - Update with correct keys
YOUTUBE_API_KEY = 'AIzaSyCVFSIGnJZk5oCIn0T9hQJg2NN8lSsFqG8'
SUPABASE_URL = 'https://uuzgosybwmzkharconxz.supabase.co'
SUPABASE_SERVICE_ROLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV1emdvc3lid216a2hhcmNvbnh6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzkzNTc3MywiZXhwIjoyMDczNTExNzczfQ.EZdRVgachRJf2cqWUnfP36ie3hNHd9vISBWN_VgrDbI'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV1emdvc3lib216a2hhcmNvbnh6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc5MzU3NzMsImV4cCI6MjA3MzUxMTc3M30.NTBm_2myHRXlRECDIqh6OFYoVmduquIgRWphc532pTU'

# Initialize clients dengan error handling
try:
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
except Exception as e:
    youtube = None

# Initialize Supabase dengan simplified approach
supabase = None
supabase_status = "❌ Not connected"

try:
    # Gunakan service_role key untuk akses penuh
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    
    # Test simple table access tanpa external request
    try:
        # Test dengan limit 0 untuk tidak fetch data tapi cek akses tabel
        result = supabase.table('youtube_videos').select('video_id').limit(0).execute()
        supabase_status = "✅ Connected"
    except Exception as table_error:
        print(f"Service role test failed: {table_error}")
        # Fallback ke anon key
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            result = supabase.table('youtube_videos').select('video_id').limit(0).execute()
            supabase_status = "✅ Connected (Anon)"
        except Exception as anon_error:
            print(f"Anon key test failed: {anon_error}")
            supabase_status = "⚠️ Database setup needed"
            
except Exception as e:
    print(f"Supabase initialization error: {e}")
    supabase = None
    supabase_status = "❌ Connection failed"

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def check_video_exists(video_id):
    """Check if video ID already exists in Supabase"""
    if not supabase:
        return False
    try:
        result = supabase.table('youtube_videos').select('video_id').eq('video_id', video_id).execute()
        exists = len(result.data) > 0
        print(f"Video {video_id} exists: {exists}")
        return exists
    except Exception as e:
        print(f"Check video error: {e}")
        return False

def insert_video_id(video_id):
    """Insert video ID to Supabase youtube_videos table"""
    if not supabase:
        return False
    try:
        # Insert tanpa ID, biarkan SERIAL auto-increment
        result = supabase.table('youtube_videos').insert({
            'video_id': video_id
        }).execute()
        print(f"Insert result: {result}")
        return True
    except Exception as e:
        print(f"Insert video error: {e}")
        error_str = str(e)
        
        # Jika error karena duplicate video_id (expected behavior)
        if "video_id" in error_str and ("duplicate" in error_str or "unique constraint" in error_str):
            print("Video already exists (duplicate video_id) - this is expected behavior")
            st.warning("⚠️ Link sudah pernah dimasukkan - video sudah pernah diproses")
            return True
            
        # Jika error karena duplicate primary key ID (sequence issue)
        if "youtube_videos_pkey" in error_str or ("Key (id)" in error_str and "already exists" in error_str):
            st.error("❌ Database sequence error! Jalankan command ini di Supabase SQL Editor:")
            st.code("""
-- Set sequence ke MAX(id) yang ada, jadi next insert = MAX(id) + 1
SELECT setval('youtube_videos_id_seq', (SELECT COALESCE(MAX(id), 0) FROM youtube_videos));
            """)
            st.info("💡 Command ini akan set sequence ke nilai terakhir, jadi insert berikutnya akan pakai MAX(id) + 1")
            return False
        
        # Error lain
        st.error(f"❌ Error menyimpan video ID: {error_str}")
        return False

def get_video_title(video_id):
    """Get video title from YouTube API"""
    try:
        request = youtube.videos().list(
            part='snippet',
            id=video_id
        )
        response = request.execute()
        
        if response['items']:
            return response['items'][0]['snippet']['title']
        else:
            return None
    except Exception as e:
        st.error(f"Error getting video title: {str(e)}")
        return None

def get_all_comments(video_id):
    """Get all comments from YouTube video using pagination"""
    comments = []
    next_page_token = None
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        while True:
            # Make API request
            request = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,  # Maximum allowed per request
                pageToken=next_page_token,
                order='time'
            )
            response = request.execute()
            
            # Process comments from current page
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'created_at': comment['publishedAt'],
                    'author_name': comment['authorDisplayName'],
                    'comment_text': comment['textDisplay'],
                    'like_count': comment.get('likeCount', 0)  # Ambil jumlah like
                })
            
            # Update progress
            status_text.text(f"Mengambil komentar... {len(comments)} komentar ditemukan")
            
            # Check if there are more pages
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
    except Exception as e:
        st.error(f"Error getting comments: {str(e)}")
        return []
    
    progress_bar.progress(100)
    status_text.text(f"Selesai! Total {len(comments)} komentar ditemukan")
    
    return comments

def save_comments_to_supabase(comments):
    """Save comments to Supabase youtube_comments table"""
    if not supabase:
        return 0
    try:
        if comments:
            # Prepare data for insertion sesuai struktur tabel
            comments_data = []
            for comment in comments:
                # Convert YouTube timestamp to PostgreSQL timestamp
                created_at = datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00'))
                comments_data.append({
                    'created_at': created_at.isoformat(),
                    'author_name': comment['author_name'],
                    'comment_text': comment['comment_text'],
                    'like_count': comment.get('like_count', 0)
                })
            
            # Insert comments in batches
            batch_size = 100  # Kurangi batch size untuk lebih stabil
            total_inserted = 0
            
            progress_bar = st.progress(0)
            for i in range(0, len(comments_data), batch_size):
                batch = comments_data[i:i+batch_size]
                try:
                    result = supabase.table('youtube_comments').insert(batch).execute()
                    total_inserted += len(batch)
                    
                    # Update progress
                    progress = int((i + len(batch)) / len(comments_data) * 100)
                    progress_bar.progress(progress)
                    st.info(f"Menyimpan... {total_inserted}/{len(comments_data)} komentar")
                    
                except Exception as batch_error:
                    st.warning(f"Error pada batch {i//batch_size + 1}: {batch_error}")
                    continue
            
            progress_bar.progress(100)
            return total_inserted
        return 0
    except Exception as e:
        st.error(f"Error menyimpan komentar: {str(e)}")
        return 0

def test_supabase_connection():
    """Test Supabase connection with simple check"""
    if not supabase:
        return False, "Not initialized"
    
    try:
        # Simple table access test
        result = supabase.table('youtube_videos').select('video_id').limit(0).execute()
        return True, "Connected"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_saved_comments_count():
    """Get total count of saved comments safely"""
    if not supabase:
        return 0
    try:
        result = supabase.table('youtube_comments').select('*', count='exact').execute()
        return result.count if result.count is not None else 0
    except Exception as e:
        return 0

def get_saved_videos_count():
    """Get total count of saved videos safely"""
    if not supabase:
        return 0
    try:
        result = supabase.table('youtube_videos').select('*', count='exact').execute()
        return result.count if result.count is not None else 0
    except Exception as e:
        return 0

def get_total_likes():
    """Get total likes from all saved comments"""
    if not supabase:
        return 0
    try:
        result = supabase.table('youtube_comments').select('like_count').execute()
        if result.data:
            return sum(comment.get('like_count', 0) for comment in result.data)
        return 0
    except Exception as e:
        return 0

def get_all_saved_comments():
    """Get all saved comments from Supabase"""
    try:
        result = supabase.table('youtube_comments').select('*').order('created_at', desc=True).execute()
        return result.data
    except Exception as e:
        st.error(f"Error getting saved comments: {str(e)}")
        return []
    """Get all saved comments from Supabase"""
    try:
        result = supabase.table('youtube_comments').select('*').order('created_at', desc=True).execute()
        return result.data
    except Exception as e:
        st.error(f"Error getting saved comments: {str(e)}")
        return []

def main():
    st.set_page_config(
        page_title="YT Dataset Harvester",
        page_icon="🎥",
        layout="wide"
    )
    
    st.title("🎥 YT Dataset Harvester")
    st.markdown("Mengumpulkan dataset dari kolom komentar YouTube untuk bahan pelatihan Model Machine Learning")
    
    # Display API status di sidebar dengan status yang sudah di-cache
    st.sidebar.header("🔧 Status API")
    
    # YouTube API Status
    if youtube:
        st.sidebar.success("✅ YouTube API: Ready")
    else:
        st.sidebar.error("❌ YouTube API: Failed")
    
    # Supabase Status - tampilkan status yang sudah dicek
    if "✅" in supabase_status:
        st.sidebar.success(supabase_status)
    elif "❌" in supabase_status:
        st.sidebar.error(supabase_status)
    else:
        st.sidebar.warning(supabase_status)
    
    # Check API status
    if not youtube:
        st.error("❌ Error: YouTube API tidak tersedia. Periksa API key.")
        return
    
    # Input section
    st.header("📝 Input YouTube Link")
    youtube_url = st.text_input(
        "Masukkan link YouTube:",
        placeholder="https://www.youtube.com/watch?v=..."
    )
    
    # Initialize session state for showing results
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False
    if 'comments_data' not in st.session_state:
        st.session_state.comments_data = None
    if 'video_title' not in st.session_state:
        st.session_state.video_title = ""
    
    if st.button("🔍 Ambil Komentar", type="primary"):
        if not youtube_url:
            st.error("❌ Silakan masukkan link YouTube terlebih dahulu!")
            return
        
        # Extract video ID
        video_id = extract_video_id(youtube_url)
        if not video_id:
            st.error("❌ Link YouTube tidak valid!")
            return
        
        st.success(f"✅ Video ID berhasil diekstrak: {video_id}")
        
        # Check if video already exists
        if supabase and "✅" in supabase_status:
            if check_video_exists(video_id):
                st.warning("⚠️ Link sudah pernah dimasukkan - video sudah pernah diproses")
                return
            
            # Insert video ID to database WAJIB
            if not insert_video_id(video_id):
                st.error("❌ Gagal menyimpan video ID ke database - proses dihentikan")
                return
            
            st.success("✅ Video ID berhasil disimpan ke database")
        else:
            st.error("❌ Database tidak tersedia - proses tidak dapat dilanjutkan")
            return
        
        # Get video title
        video_title = get_video_title(video_id)
        if not video_title:
            st.error("❌ Gagal mendapatkan judul video")
            return
        
        st.session_state.video_title = video_title
        st.subheader(f"🎬 Judul Video: {video_title}")
        
        # Get all comments
        st.info("📥 Mengambil komentar dari YouTube...")
        comments = get_all_comments(video_id)
        
        if not comments:
            st.warning("⚠️ Tidak ada komentar yang ditemukan atau terjadi error")
            return
        
        # Save comments to Supabase - WAJIB
        st.info("💾 Menyimpan komentar ke database...")
        saved_count = save_comments_to_supabase(comments)
        
        if saved_count > 0:
            st.success(f"✅ Berhasil menyimpan {saved_count} komentar ke database!")
        else:
            st.error("❌ Gagal menyimpan komentar ke database")
            return
        
        # Store data in session state
        st.session_state.comments_data = comments
        st.session_state.show_results = True
    
    # Show results only after button click
    if st.session_state.show_results and st.session_state.comments_data:
        # Display comments in table
        st.subheader(f"📊 Daftar Komentar ({len(st.session_state.comments_data)} komentar)")
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(st.session_state.comments_data)
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Display scrollable table
        st.dataframe(
            df,
            use_container_width=True,
            height=400,
            column_config={
                "created_at": "Waktu",
                "author_name": "Nama Penulis",
                "comment_text": "Komentar",
                "like_count": "👍 Likes"
            }
        )
        
        # Statistics section - Only show after results
        st.header("📈 Statistik Database")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_videos = get_saved_videos_count()
            st.metric("Total Video", total_videos)
        
        with col2:
            total_comments = get_saved_comments_count()
            st.metric("Total Komentar", total_comments)
        
        with col3:
            total_likes = get_total_likes()
            st.metric("👍 Total Likes", total_likes)
        
        # Display all saved comments - Only show after results
        if st.checkbox("📋 Tampilkan Semua Komentar Tersimpan"):
            st.subheader("🗂️ Semua Komentar Tersimpan")
            all_comments = get_all_saved_comments()
            
            if all_comments:
                df_all = pd.DataFrame(all_comments)
                df_all['created_at'] = pd.to_datetime(df_all['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
                
                st.dataframe(
                    df_all[['created_at', 'author_name', 'comment_text', 'like_count']],
                    use_container_width=True,
                    height=400,
                    column_config={
                        "created_at": "Waktu",
                        "author_name": "Nama Penulis",
                        "comment_text": "Komentar",
                        "like_count": "👍 Likes"
                    }
                )
            else:
                st.info("Belum ada komentar tersimpan")

if __name__ == "__main__":
    main()
