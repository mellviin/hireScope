import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Resume {
  id: number;
  filename: string;
  file_type: string;
  created_at: string;
  parsed_data?: any;
}

interface ResumeState {
  resumes: Resume[];
  currentResume: Resume | null;
  isLoading: boolean;
  error: string | null;
  uploadProgress: number;
}

const initialState: ResumeState = {
  resumes: [],
  currentResume: null,
  isLoading: false,
  error: null,
  uploadProgress: 0,
};

const resumeSlice = createSlice({
  name: 'resume',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setResumes: (state, action: PayloadAction<Resume[]>) => {
      state.resumes = action.payload;
    },
    setCurrentResume: (state, action: PayloadAction<Resume>) => {
      state.currentResume = action.payload;
    },
    addResume: (state, action: PayloadAction<Resume>) => {
      state.resumes.push(action.payload);
    },
    removeResume: (state, action: PayloadAction<number>) => {
      state.resumes = state.resumes.filter((r) => r.id !== action.payload);
      if (state.currentResume?.id === action.payload) {
        state.currentResume = null;
      }
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setUploadProgress: (state, action: PayloadAction<number>) => {
      state.uploadProgress = action.payload;
    },
  },
});

export const { setLoading, setResumes, setCurrentResume, addResume, removeResume, setError, setUploadProgress } = resumeSlice.actions;
export default resumeSlice.reducer;
