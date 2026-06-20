import { AppDispatch } from '../redux/store';
import { authAPI, resumeAPI, jdAPI } from '../services/api';
import { setUser, logout } from '../redux/slices/authSlice';
import { setResumes } from '../redux/slices/resumeSlice';
import { setJobDescriptions } from '../redux/slices/jobDescriptionSlice';

export const loadUserData = async (dispatch: AppDispatch) => {
  const [resumesRes, jdsRes] = await Promise.all([
    resumeAPI.listResumes(),
    jdAPI.listJDs(),
  ]);
  dispatch(setResumes(resumesRes.data));
  dispatch(setJobDescriptions(jdsRes.data));
};

export const restoreSession = async (dispatch: AppDispatch) => {
  try {
    const [userRes, resumesRes, jdsRes] = await Promise.all([
      authAPI.getCurrentUser(),
      resumeAPI.listResumes(),
      jdAPI.listJDs(),
    ]);
    dispatch(setUser(userRes.data));
    dispatch(setResumes(resumesRes.data));
    dispatch(setJobDescriptions(jdsRes.data));
  } catch {
    dispatch(logout());
  }
};
