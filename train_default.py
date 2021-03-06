import pandas as pd
import numpy as np
import glob, sys
from datetime import date
import pickle
from random import randint
from datetime import datetime

from sklearn.cross_validation import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor 
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn import preprocessing
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report

from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

from sklearn.tree import export_graphviz 
from sklearn.decomposition import PCA
from sklearn.metrics import recall_score

from scipy.stats import randint as sp_randint
import matplotlib.pyplot as plt

class Trainer():
	def __init__(self):
		self.load_data('mysql_dump.pickle')
		self.drop_columns()
		self.loanData = self.loanData.dropna()
		self.loanData.index = range(len(self.loanData))
		self.originalLoanData.index = range(len(self.originalLoanData))
		self.drop_some_pos_samples()
		self.split_train_test()

	def load_data(self, fileName):
		print "Loading %s" %fileName
		f = open(fileName, 'rb')
		self.loanData = pickle.load(f)
		self.originalLoanData = self.loanData	#including dropped columns

	def drop_columns(self):
		self.loanData = self.loanData.drop(['Any', 
											'issue_d', 
											'last_pymnt_d',
											'unemp_rate_3mths',
											'unemp_rate_6mths',
											'unemp_rate_12mths',
											'days_active'
											], 1)

	def drop_some_pos_samples(self):
		for i in range(30000):
			if self.loanData['loan_status'][i] == 1:
				self.loanData['loan_status'].iloc[i] = 3
				self.originalLoanData['loan_status'].iloc[i] = 3
		self.loanData = self.loanData[self.loanData['loan_status'] != 3]
		self.originalLoanData = self.originalLoanData[self.originalLoanData['loan_status'] != 3]

	def split_train_test(self, test_size=0.2):

		features = self.loanData.drop(['loan_status'], 1).values
		targets = self.loanData['loan_status'].values
		self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(features, 
																	targets, 
																	test_size=test_size)
		self.X_train = self.X_train.astype(float)
		self.y_train = self.y_train.astype(float)
		self.X_test = self.X_test.astype(float)
		self.y_test = self.y_test.astype(float)

		print "Loans in training set: ", len(self.y_train)
		print "Defaults in training set: ", np.sum(self.y_train == 0)
		print "Loans in testing set: ", len(self.y_test)
		print "Defaults in testing set: ", np.sum(self.y_test == 0)


	def scale(self):
		self.scalerX = StandardScaler().fit(self.X_train)
		self.X_train, self.X_test = self.scalerX.transform(self.X_train), \
									self.scalerX.transform(self.X_test)

	def standardize_samples(self):
		##0 mean, unit variance
		self.X_train = preprocessing.scale(self.X_train)
		self.X_test = preprocessing.scale(self.X_test)

	def scale_samples_to_range(self):
		##Samples lie in range between 0 and 1
		minMaxScaler = preprocessing.MinMaxScaler()
		self.X_train = minMaxScaler.fit_transform(self.X_train)
		self.X_test = minMaxScaler.fit_transform(self.X_test)

	def run_pca(self, n_components=20):
		self.pca = PCA(n_components=n_components)
		self.X_train = self.pca.fit_transform(self.X_train)
		print "Reduced data down to ", self.pca.n_components_, " dimensions: "
		print "Transforming test data ..."
		self.X_test = self.pca.transform(self.X_test)

	def define_rfc(self, n_estimators=20):
		self.clf = RandomForestClassifier(n_estimators=n_estimators)
		print self.clf.get_params()

	def defineSVC(self, C=1.0, kernel='rbf', degree=3, gamma=0.0, coef0=0.0, shrinking=True, 
				  probability=False, tol=0.01, cache_size=200, class_weight='auto', verbose=True, 
				  max_iter=-1, random_state=None):

		print "Using a Support Vector Machine Classifier ..."
		self.clf = SVC(C=C, kernel=kernel, degree=degree, gamma=gamma, coef0=coef0, shrinking=shrinking, 
				  probability=probability, tol=tol, cache_size=cache_size, class_weight=class_weight, verbose=verbose, 
				  max_iter=max_iter, random_state=random_state)
		print self.clf.get_params()

	def train(self):
		print "training classifier"
		self.clf.fit(self.X_train, self.y_train)

	def score(self, y_actual, pred):
		print classification_report(y_actual, pred)
		print "predict 0: ", np.sum(pred == 0)
		print "predict 1: ", np.sum(pred == 1)
		print "actual 0: ", np.sum(y_actual == 0)
		print "actual 0: ", np.sum(y_actual == 1)
		#print "feature importances:"
		#print self.clf.feature_importances_

	def predict(self, X):
		print "predicting"
		self.prediction = self.clf.predict(X)

	def confusion_mat(self):
		cm = confusion_matrix(self.y_test, self.prediction)
		plt.matshow(cm)
		plt.title('Confusion matrix')
		plt.colorbar()
		plt.ylabel('True label')
		plt.xlabel('Predicted label')
		plt.show()

	def runSVCGridSearch(self):
		C_vals = [0.01, 0.1, 1, 10, 100]
		gamma_vals = [1E-2, 1E-1, 1, 1E1, 1E2, 1E3, 1E4]

		for C in C_vals:
			for gamma in gamma_vals:
				print "\n\n C: ", C, "  gamma: ", gamma
				self.defineSVC(C=C, gamma=gamma)
				self.train()
				print "Training Scores:"
				self.predict(self.X_train)
				self.score(self.y_train, self.prediction)
				print "Testing Scores:"
				self.predict(self.X_test)
				self.score(self.y_test, self.prediction)
	def print_predicted_defaults(self, y, pred):
		#tpr == predict paid, actually paid rate (ie recall)
		tpr = np.sum((pred == 1) & (y == 1))*1.0 / np.sum(y == 1)
		#fpr == predict paid, actually default rate
		fpr = np.sum((pred == 1) & (y == 0))*1.0 / np.sum(y == 0)
		#fnr == predict default actually paid rate
		fnr = np.sum((pred == 0) & (y == 1))*1.0 / np.sum(y == 1)
		#tnr == predict default actually default rate (ie specificity)
		tnr = np.sum((pred == 0) & (y == 0))*1.0 / np.sum(y == 0)

		print "tpr - predict_paid_actually_paid: " + str(tpr)
		print "fpr - predict_paid_actually_default: " + str(fpr)
		print "fnr - predict_default_actually_paid: " + str(fnr)
		print "tnr - predict_default_actually_default: " + str(tnr)

	def save_loans_pred_to_default(self):
		pred_defaults = [self.originalLoanData.iloc[i] for i,val in enumerate(self.prediction) if val==0]
		print "pickling"
		f = open('pred_defaults.pickle', 'wb')
		pickle.dump(pred_defaults, f)
		f.close()

trainer = Trainer()
#trainer.standardize_samples()
#trainer.scale_samples_to_range()

#trainer.run_pca(50)


n_trees = [100]
for n in n_trees:
	trainer.define_rfc(n_estimators=n)
	trainer.train()
	trainer.predict(trainer.X_test)
	trainer.score(trainer.y_test, trainer.prediction)
	trainer.print_predicted_defaults(trainer.y_test, trainer.prediction)
trainer.save_loans_pred_to_default()

