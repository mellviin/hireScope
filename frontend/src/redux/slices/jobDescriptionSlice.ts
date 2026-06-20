import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface JobDescription {
  id: number;
  job_title: string;
  company?: string;
  created_at: string;
  parsed_data?: any;
}

interface JobDescriptionState {
  jobDescriptions: JobDescription[];
  currentJD: JobDescription | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: JobDescriptionState = {
  jobDescriptions: [],
  currentJD: null,
  isLoading: false,
  error: null,
};

const jobDescriptionSlice = createSlice({
  name: 'jobDescription',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setJobDescriptions: (state, action: PayloadAction<JobDescription[]>) => {
      state.jobDescriptions = action.payload;
    },
    setCurrentJD: (state, action: PayloadAction<JobDescription>) => {
      state.currentJD = action.payload;
    },
    addJobDescription: (state, action: PayloadAction<JobDescription>) => {
      state.jobDescriptions.push(action.payload);
    },
    removeJobDescription: (state, action: PayloadAction<number>) => {
      state.jobDescriptions = state.jobDescriptions.filter((jd) => jd.id !== action.payload);
      if (state.currentJD?.id === action.payload) {
        state.currentJD = null;
      }
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const { setLoading, setJobDescriptions, setCurrentJD, addJobDescription, removeJobDescription, setError } = jobDescriptionSlice.actions;
export default jobDescriptionSlice.reducer;
