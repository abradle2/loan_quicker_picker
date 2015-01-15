import pandas as pd
import numpy as np
import glob, sys
from datetime import date
import pickle

##Load Data
files = glob.glob('./data/*.csv')
list1 = []
for fileName in files:
    tempFrame = pd.read_csv(fileName, header=1)
    list1.append(tempFrame)
loanData = pd.concat(list1, ignore_index=True)



##int_rate
print "int_rate"
loanData['int_rate'] = loanData['int_rate'].str.replace('%', '')
loanData['int_rate'] = loanData['int_rate'].astype(float)


##term
print "term"
loanData['term'] = [0 if x == " 36 months" else 1 for x in loanData['term']]



##grade
print "grade"
loanData = loanData[pd.isnull(loanData['grade']) == 0]
loanData.index = range(len(loanData))
print "loans: ", len(loanData)



#grades = dict(zip(loanData['grade'].unique(), np.arange(loanData['grade'].nunique())))
#loanData['grade'] = loanData['grade'].map(lambda x: grades[x])


#Binarize the grade
gradesBinarized = pd.get_dummies(loanData['grade'])
loanData = pd.concat([loanData, gradesBinarized], axis=1)
loanData = loanData.drop(['grade'], 1)


#Subgrade - numeric part of LendingClub's subgrade (ie: b3 -> grade=b, subgrade=3)
loanData['sub_grade'] = [x[1:] for x in loanData['sub_grade']]


##emp_length
print "emp_length"
emp_years = dict(zip(loanData['emp_length'].unique(), np.arange(loanData['emp_length'].nunique())))
loanData['emp_length'] = loanData['emp_length'].map(lambda x: emp_years[x])


##home_ownership
#loanData['home_ownership'] = ["None" if pd.isnull(x) else x for x in loanData['home_ownership']]
#ownership_dict = dict(zip(loanData['home_ownership'].unique(), np.arange(loanData['home_ownership'].nunique())))
#loanData['home_ownership'] = loanData['home_ownership'].map(lambda x: ownership_dict[x])


homeOwnershipBinarized = pd.get_dummies(loanData['home_ownership'])
loanData = pd.concat([loanData, homeOwnershipBinarized], axis=1)
loanData = loanData.drop(['home_ownership'], 1)



##is_inc_v
#possible values:
#	Source Verified
#	Verified
#	Not Verified
loanData['is_inc_v'] = [1 if x == "Source Verified" else x for x in loanData['is_inc_v']]
loanData['is_inc_v'] = [2 if x == "Verified" else x for x in loanData['is_inc_v']]
loanData['is_inc_v'] = [0 if x == "Not Verified" else x for x in loanData['is_inc_v']]



##issue_month and issue_year
print "issue_month"
loanData['issue_month'] = 0
loanData['issue_year'] = 0
for i in range(len(loanData['issue_d'])):
    m = pd.to_datetime(loanData['issue_d'][i]).month
    y = pd.to_datetime(loanData['issue_d'][i]).year
    loanData['issue_month'][i] = m
    loanData['issue_year'][i] = y

loanData = loanData.drop('issue_d', 1)



##pymnt_plan
#loanData['pymnt_plan'] = [1 if x == 'y' else 0 for x in loanData['pymnt_plan']]
loanData = loanData.drop(["pymnt_plan"], 1) 


##purpose
print "purpose"
purposeBinarized = pd.get_dummies(loanData['purpose'])
loanData = pd.concat([loanData, purposeBinarized], axis=1)
loanData = loanData.drop('purpose', 1)

##zip_code
loanData['zip_code'] = [x[:3] for x in loanData['zip_code']]


##addr_state
statesBinarized = pd.get_dummies(loanData['addr_state'])
loanData = pd.concat([loanData, statesBinarized], axis=1)
loanData = loanData.drop('addr_state', 1)


##yrs_since_first_cr_line
print "yrs_since_first_cr_line"
loanData['yrs_since_first_cr_line'] = 0
for i in range(len(loanData['earliest_cr_line'])):
    earliest_year = pd.to_datetime(loanData['earliest_cr_line'][i]).year
    loanData['yrs_since_first_cr_line'][i] = date.today().year - earliest_year
loanData = loanData.drop('earliest_cr_line', 1)


##delinquencies
loanData['mths_since_last_delinq'] = [-1 if pd.isnull(x) else x for x in loanData['mths_since_last_delinq']]


##records
print "records"
loanData['mths_since_last_record'] = [-1 if pd.isnull(x) else x for x in loanData['mths_since_last_record']]


##revol_util
loanData['revol_util'] = loanData['revol_util'].str.replace('%', '')
loanData['revol_util'] = loanData['revol_util'].astype(float)
loanData['revol_util'] = [-1 if pd.isnull(x) else x for x in loanData['revol_util']]


##initial_list_status
print "initial_list_status"
loanData['initial_list_status'] = [1 if x in ['w', 'W'] else 0 for x in loanData['initial_list_status']]


##major_derog
loanData['mths_since_last_major_derog'] = [-1 if pd.isnull(x) else x for x in loanData['mths_since_last_major_derog']]


##collections_12_mths_ex_med
loanData['collections_12_mths_ex_med'] = [-1 if pd.isnull(x) else x for x in loanData['collections_12_mths_ex_med']]


##remove all non-finished loans
print "loan_status"
loanData = loanData[[x in ['Charged Off',
						   'Default', 
						   'Fully Paid', 
						   'Does not meet the credit policy.  Status:Charged Off',
						   'Does not meet the credit policy.  Status:Default',
						   'Does not meet the credit policy.  Status:Fully Paid'
						   ] for x in loanData['loan_status']]]
loanData.index = range(len(loanData))
print "loans: ", len(loanData)

##Remove features which aren't available for new loan listings
print "removing features"
#loanData = loanData.drop('total_pymnt', 1)
loanData = loanData.drop('initial_list_status', 1)
loanData = loanData.drop('policy_code', 1)


loanData['loan_status'] = [0 if x in ['Charged Off',
						   			  'Default',
								      'Does not meet the credit policy.  Status:Charged Off',
								      'Does not meet the credit policy.  Status:Default'
						   			 ] else 1 for x in loanData['loan_status'] ]


##desc_length
print "putting in lengths of string features"
loanData['desc_length'] = [len(str(x)) for x in loanData['desc']]

##title_length
loanData['title_length'] = [len(str(x)) for x in loanData['title']]

##emp_title
loanData['emp_title'] = [len(str(x)) for x in loanData['emp_title']]


loanData = loanData.drop(["member_id", 
						  "id", 
						  "url", 
						  "out_prncp", 
						  "out_prncp_inv", 
						  "total_pymnt_inv", 
						  "total_rec_prncp", 
						  "total_rec_int", 
						  "total_rec_late_fee",
						  "recoveries", 
						  "collection_recovery_fee", 
						  "last_pymnt_amnt",
						  "desc", 
						  "title",
						  "emp_title",
						  "last_pymnt_d",
						  "last_credit_pull_d",
						  "last_pymnt_amnt",
						  "next_pymnt_d"
						  ], 1)



##Drop loans with missing values
print "dropping NAs"
loanData = loanData.dropna()
loanData.index = range(len(loanData))
print "loans: ", len(loanData)



##Pickle the dataframe
print "pickling"
f = open('data.pickle', 'wb')
pickle.dump(loanData, f)
f.close()


