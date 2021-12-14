#importing necessary libraries

import pandas as pd
import pickle
import os
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer


path = os.getcwd() + "//OneDrive//Desktop//Flotilla Techs//Metadata_based_recommendation//metadata_model"
course_metadata = pd.read_csv(path + '//course_info.csv')
course_metadata['metadata'] = course_metadata.apply(lambda x : ''.join(x['CourseName']) + ' ' + ''.join(x['SubjectName']) + ' ' + ''.join(x['SkillName']) + ' ' + ''.join(x['ProviderName']), axis = 1)

count_vec = CountVectorizer(stop_words='english')
count_vec_matrix = count_vec.fit_transform(course_metadata['metadata'])

cosine_sim_matrix = cosine_similarity(count_vec_matrix, count_vec_matrix)

filename = path + "//metadata_based_dump.sav"
with open(filename, 'wb') as f:
    pickle.dump(cosine_sim_matrix, f)
    

mapping = pd.DataFrame({'CourseId':course_metadata['CourseId'], 'CourseName':course_metadata['CourseName'], 'CourseIndex':course_metadata.index})

filename = path + "//metadata_mapping_dump.sav"
with open(filename, 'wb') as f:
    pickle.dump(mapping, f)

